import type { Session } from '@supabase/supabase-js'

import {
  ApiError,
  type MeResponse,
  type RoleCode,
  type WorkspaceResponse,
} from '../../lib/api/client'

export type AuthState =
  | { status: 'configuration_missing'; message: string }
  | { status: 'loading' }
  | { status: 'signed_out' }
  | { status: 'ready'; identity: MeResponse }
  | { status: 'error'; message: string; code?: string }

export interface AuthSnapshot {
  state: AuthState
  hasSession: boolean
}

export interface AuthGateway {
  getSession: () => Promise<{
    data: { session: Session | null }
    error: unknown | null
  }>
  onAuthStateChange: (callback: (session: Session | null) => void) => () => void
  signInWithPassword: (credentials: { email: string; password: string }) => Promise<{
    data: { session: Session | null }
    error: unknown | null
  }>
  signOut: () => Promise<unknown>
}

export interface AuthSessionDependencies {
  auth: AuthGateway | null
  getMe: (accessToken: string) => Promise<MeResponse>
  getWorkspace: (role: RoleCode, accessToken: string) => Promise<WorkspaceResponse>
}

type SnapshotListener = (snapshot: AuthSnapshot) => void

const configurationMessage = '当前环境尚未配置登录服务'

function publicIdentityError(error: unknown): { message: string; code?: string } {
  if (error instanceof ApiError) return { message: error.message, code: error.code }
  return { message: '暂时无法读取当前应用身份' }
}

/**
 * Owns auth/session async ordering independently from React rendering.
 * Every new session event invalidates older restore and identity requests.
 */
export class AuthSessionCoordinator {
  private readonly listeners = new Set<SnapshotListener>()
  private snapshot: AuthSnapshot
  private session: Session | null = null
  private revision = 0
  private active = false
  private unsubscribeAuth: (() => void) | null = null

  constructor(private readonly dependencies: AuthSessionDependencies) {
    this.snapshot = dependencies.auth
      ? { state: { status: 'loading' }, hasSession: false }
      : {
          state: { status: 'configuration_missing', message: configurationMessage },
          hasSession: false,
        }
  }

  getSnapshot(): AuthSnapshot {
    return this.snapshot
  }

  getAccessToken(): string | null {
    return this.session?.access_token ?? null
  }

  subscribe(listener: SnapshotListener): () => void {
    this.listeners.add(listener)
    listener(this.snapshot)
    return () => this.listeners.delete(listener)
  }

  start(): () => void {
    const { auth } = this.dependencies
    if (!auth || this.active) return () => undefined

    this.active = true
    this.publish({ status: 'loading' })
    this.unsubscribeAuth = auth.onAuthStateChange((session) => {
      this.acceptAuthEvent(session)
    })
    void this.restoreSession()

    return () => this.stop()
  }

  stop(): void {
    if (!this.active) return
    this.active = false
    this.revision += 1
    this.unsubscribeAuth?.()
    this.unsubscribeAuth = null
  }

  async signIn(email: string, password: string): Promise<string | null> {
    const { auth } = this.dependencies
    if (!auth) return configurationMessage

    const revision = ++this.revision
    try {
      const { data, error } = await auth.signInWithPassword({ email, password })
      if (error || !data.session) {
        return '邮箱或密码不正确，或登录服务暂不可用'
      }
      // Supabase normally emits SIGNED_IN before this promise settles. If it did,
      // that newer event already owns identity resolution and this is a no-op.
      if (this.isCurrent(revision)) await this.resolveSession(data.session, revision)
      return null
    } catch {
      return '邮箱或密码不正确，或登录服务暂不可用'
    }
  }

  async signOut(): Promise<void> {
    this.revision += 1
    this.session = null
    this.publish({ status: 'signed_out' })

    const { auth } = this.dependencies
    if (!auth) return
    try {
      await auth.signOut()
    } catch {
      // The in-memory session and protected content are already cleared. A
      // later auth event or retry will reconcile the persisted session.
    }
  }

  async retry(): Promise<void> {
    if (!this.dependencies.auth) {
      this.publish({ status: 'configuration_missing', message: configurationMessage })
      return
    }
    await this.restoreSession()
  }

  authorizeRole(role: RoleCode): Promise<WorkspaceResponse> {
    const session = this.session
    if (!session) throw new ApiError('登录状态已失效', 401, { code: 'AUTH_REQUIRED' })
    return this.dependencies.getWorkspace(role, session.access_token)
  }

  private async restoreSession(): Promise<void> {
    const { auth } = this.dependencies
    if (!auth) return

    const revision = ++this.revision
    this.publish({ status: 'loading' })
    try {
      const { data, error } = await auth.getSession()
      if (!this.isCurrent(revision)) return
      if (error) {
        this.publish({ status: 'error', message: '暂时无法恢复登录状态' })
        return
      }
      await this.resolveSession(data.session, revision)
    } catch {
      if (this.isCurrent(revision)) {
        this.publish({ status: 'error', message: '暂时无法恢复登录状态' })
      }
    }
  }

  private acceptAuthEvent(session: Session | null): void {
    if (!this.active) return

    const currentToken = this.session?.access_token ?? null
    const nextToken = session?.access_token ?? null
    const currentStatus = this.snapshot.state.status
    if (
      currentToken === nextToken
      && (currentStatus === 'loading' || currentStatus === 'ready' || currentStatus === 'signed_out')
    ) {
      return
    }

    const revision = ++this.revision
    void this.resolveSession(session, revision)
  }

  private async resolveSession(session: Session | null, revision: number): Promise<void> {
    if (!this.isCurrent(revision)) return
    this.session = session
    if (!session) {
      this.publish({ status: 'signed_out' })
      return
    }

    this.publish({ status: 'loading' })
    try {
      const identity = await this.dependencies.getMe(session.access_token)
      if (this.isCurrent(revision)) this.publish({ status: 'ready', identity })
    } catch (error) {
      if (this.isCurrent(revision)) this.publish({ status: 'error', ...publicIdentityError(error) })
    }
  }

  private isCurrent(revision: number): boolean {
    return this.active && revision === this.revision
  }

  private publish(state: AuthState): void {
    this.snapshot = { state, hasSession: this.session !== null }
    for (const listener of this.listeners) listener(this.snapshot)
  }
}

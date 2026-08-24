import { ApiError, type RoleCode, type WorkspaceResponse } from '../../lib/api/client'

export type RoleAuthorizationState =
  | { status: 'checking' }
  | { status: 'allowed'; workspace: WorkspaceResponse }
  | { status: 'denied' }
  | { status: 'error'; message: string }

export interface RoleAuthorizationSnapshot {
  key: string
  state: RoleAuthorizationState
}

type AuthorizeRole = (role: RoleCode) => Promise<WorkspaceResponse>
type SnapshotListener = (snapshot: RoleAuthorizationSnapshot) => void

/** Coordinates one active authorization check and drops every older result. */
export class RoleAuthorizationCoordinator {
  private readonly listeners = new Set<SnapshotListener>()
  private snapshot: RoleAuthorizationSnapshot = { key: '', state: { status: 'checking' } }
  private revision = 0

  constructor(private readonly authorizeRole: AuthorizeRole) {}

  getSnapshot(): RoleAuthorizationSnapshot {
    return this.snapshot
  }

  subscribe(listener: SnapshotListener): () => void {
    this.listeners.add(listener)
    listener(this.snapshot)
    return () => this.listeners.delete(listener)
  }

  check(key: string, role: RoleCode): () => void {
    const revision = ++this.revision
    this.publish({ key, state: { status: 'checking' } })

    void Promise.resolve()
      .then(() => this.authorizeRole(role))
      .then((workspace) => {
        if (revision === this.revision) {
          this.publish({ key, state: { status: 'allowed', workspace } })
        }
      })
      .catch((error: unknown) => {
        if (revision !== this.revision) return
        if (error instanceof ApiError && error.status === 403) {
          this.publish({ key, state: { status: 'denied' } })
          return
        }
        this.publish({
          key,
          state: {
            status: 'error',
            message: error instanceof ApiError ? error.message : '暂时无法确认工作区权限',
          },
        })
      })

    return () => {
      if (revision === this.revision) this.revision += 1
    }
  }

  clear(): void {
    this.revision += 1
    this.publish({ key: '', state: { status: 'checking' } })
  }

  private publish(snapshot: RoleAuthorizationSnapshot): void {
    this.snapshot = snapshot
    for (const listener of this.listeners) listener(snapshot)
  }
}

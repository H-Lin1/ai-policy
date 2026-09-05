import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'

import {
  apiClient,
  type RoleCode,
  type WorkspaceResponse,
} from '../../lib/api/client'
import {
  AuthSessionCoordinator,
  type AuthGateway,
  type AuthSession,
  type AuthState,
} from './AuthSessionCoordinator'

export type { AuthState } from './AuthSessionCoordinator'

export interface AuthContextValue {
  state: AuthState
  hasSession: boolean
  signIn: (username: string, password: string) => Promise<string | null>
  signOut: () => Promise<void>
  retry: () => void
  authorizeRole: (role: RoleCode) => Promise<WorkspaceResponse>
  getAccessToken: () => string | null
}

export const AuthContext = createContext<AuthContextValue | undefined>(undefined)

const AUTH_STORAGE_KEY = 'ai-policy-local-auth'

function readStoredSession(): AuthSession | null {
  try {
    const raw = window.localStorage.getItem(AUTH_STORAGE_KEY)
    if (!raw) return null
    const parsed = JSON.parse(raw) as { access_token?: unknown }
    return typeof parsed.access_token === 'string' && parsed.access_token
      ? { access_token: parsed.access_token }
      : null
  } catch {
    return null
  }
}

function createAuthGateway(): AuthGateway {
  return {
    getSession: async () => ({ data: { session: readStoredSession() }, error: null }),
    onAuthStateChange: () => () => undefined,
    signInWithPassword: async ({ username, password }) => {
      try {
        const data = await apiClient.login(username, password)
        const session: AuthSession = { access_token: data.access_token }
        window.localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(session))
        return { data: { session }, error: null }
      } catch (error) {
        return { data: { session: null }, error }
      }
    },
    signOut: async () => {
      window.localStorage.removeItem(AUTH_STORAGE_KEY)
      return { error: null }
    },
  }
}

const authGateway = createAuthGateway()

export function AuthProvider({ children }: { children: ReactNode }) {
  const [coordinator] = useState(
    () => new AuthSessionCoordinator({
      auth: authGateway,
      getMe: apiClient.getMe,
      getWorkspace: apiClient.getWorkspace,
    }),
  )
  const [snapshot, setSnapshot] = useState(() => coordinator.getSnapshot())

  useEffect(() => {
    const unsubscribeSnapshot = coordinator.subscribe(setSnapshot)
    const stop = coordinator.start()
    return () => {
      stop()
      unsubscribeSnapshot()
    }
  }, [coordinator])

  const signIn = useCallback(
    (username: string, password: string) => coordinator.signIn(username, password),
    [coordinator],
  )
  const signOut = useCallback(() => coordinator.signOut(), [coordinator])
  const retry = useCallback(() => void coordinator.retry(), [coordinator])
  const authorizeRole = useCallback(
    (role: RoleCode) => coordinator.authorizeRole(role),
    [coordinator],
  )
  const getAccessToken = useCallback(() => coordinator.getAccessToken(), [coordinator])

  const value = useMemo<AuthContextValue>(
    () => ({
      state: snapshot.state,
      hasSession: snapshot.hasSession,
      signIn,
      signOut,
      retry,
      authorizeRole,
      getAccessToken,
    }),
    [snapshot, signIn, signOut, retry, authorizeRole, getAccessToken],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthContextValue {
  const value = useContext(AuthContext)
  if (!value) throw new Error('useAuth must be used inside AuthProvider')
  return value
}

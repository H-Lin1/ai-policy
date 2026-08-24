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
import { supabase, supabaseAuthConfigured } from './supabase'
import {
  AuthSessionCoordinator,
  type AuthGateway,
  type AuthState,
} from './AuthSessionCoordinator'

export type { AuthState } from './AuthSessionCoordinator'

export interface AuthContextValue {
  state: AuthState
  hasSession: boolean
  signIn: (email: string, password: string) => Promise<string | null>
  signOut: () => Promise<void>
  retry: () => void
  authorizeRole: (role: RoleCode) => Promise<WorkspaceResponse>
  getAccessToken: () => string | null
}

export const AuthContext = createContext<AuthContextValue | undefined>(undefined)

function createAuthGateway(): AuthGateway | null {
  const client = supabase
  if (!supabaseAuthConfigured || !client) return null
  return {
    getSession: () => client.auth.getSession(),
    onAuthStateChange: (callback) => {
      const { data } = client.auth.onAuthStateChange((_event, session) => callback(session))
      return () => data.subscription.unsubscribe()
    },
    signInWithPassword: (credentials) => client.auth.signInWithPassword(credentials),
    signOut: () => client.auth.signOut(),
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
    (email: string, password: string) => coordinator.signIn(email, password),
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

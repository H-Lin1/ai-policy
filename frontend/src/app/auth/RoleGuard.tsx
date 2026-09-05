import { useEffect, useState, type ReactNode } from 'react'

import type { RoleCode, WorkspaceResponse } from '../../lib/api/client'
import { useAuth, type AuthState } from './AuthProvider'
import {
  RoleAuthorizationCoordinator,
  type RoleAuthorizationState,
} from './RoleAuthorizationCoordinator'

export type { RoleAuthorizationState } from './RoleAuthorizationCoordinator'

interface RoleGuardViewProps {
  authState: AuthState
  authorization: RoleAuthorizationState
  retryIdentity: () => void
  retryAuthorization: () => void
  children: (workspace: WorkspaceResponse) => ReactNode
}

export function RoleGuardView({
  authState,
  authorization,
  retryIdentity,
  retryAuthorization,
  children,
}: RoleGuardViewProps) {
  const appBasePath = (import.meta.env.VITE_APP_BASE_PATH ?? '/').replace(/\/+$/, '')
  if (authState.status === 'configuration_missing') {
    return <AccessState title="登录服务未配置" message={authState.message} />
  }
  if (authState.status === 'loading') {
    return <AccessState title="正在读取身份" message="正在核对登录状态与应用权限。" pending />
  }
  if (authState.status === 'signed_out') {
    return (
      <AccessState title="需要登录" message="登录后可进入已授权的工作区。">
        <a className="button button-primary" href={`${appBasePath || ''}/login`}>登录</a>
      </AccessState>
    )
  }
  if (authState.status === 'error') {
    return (
      <AccessState title="身份暂不可用" message={authState.message}>
        <button type="button" className="button button-primary" onClick={retryIdentity}>重试</button>
      </AccessState>
    )
  }
  if (authorization.status === 'checking') {
    return <AccessState title="正在确认权限" message="正在核对该工作区的服务端授权。" pending />
  }
  if (authorization.status === 'denied') {
    return <AccessState title="无权访问" message="当前应用身份未获准进入该工作区。" />
  }
  if (authorization.status === 'error') {
    return (
      <AccessState title="权限服务暂不可用" message={authorization.message}>
        <button type="button" className="button button-primary" onClick={retryAuthorization}>重试</button>
      </AccessState>
    )
  }
  return <>{children(authorization.workspace)}</>
}

export function RoleGuard({
  role,
  children,
}: {
  role: RoleCode
  children: (workspace: WorkspaceResponse) => ReactNode
}) {
  const { state: authState, authorizeRole, retry: retryIdentity } = useAuth()
  const authorizationKey = `${role}:${authState.status === 'ready' ? authState.identity.subject : ''}`
  const [coordinator] = useState(() => new RoleAuthorizationCoordinator(authorizeRole))
  const [authorizationResult, setAuthorizationResult] = useState(() => coordinator.getSnapshot())
  const authorization =
    authorizationResult.key === authorizationKey
      ? authorizationResult.state
      : { status: 'checking' as const }

  useEffect(() => {
    return coordinator.subscribe(setAuthorizationResult)
  }, [coordinator])

  useEffect(() => {
    if (authState.status !== 'ready') {
      coordinator.clear()
      return undefined
    }
    return coordinator.check(authorizationKey, role)
  }, [authState.status, authorizationKey, coordinator, role])

  return (
    <RoleGuardView
      authState={authState}
      authorization={authorization}
      retryIdentity={retryIdentity}
      retryAuthorization={() => {
        if (authState.status === 'ready') coordinator.check(authorizationKey, role)
      }}
    >
      {children}
    </RoleGuardView>
  )
}

function AccessState({
  title,
  message,
  pending = false,
  children,
}: {
  title: string
  message: string
  pending?: boolean
  children?: ReactNode
}) {
  return (
    <section className="page-content access-state" aria-live="polite" aria-busy={pending}>
      <div className="eyebrow">身份与权限</div>
      <h1>{title}</h1>
      <p className="lead">{message}</p>
      {children ? <div className="state-actions">{children}</div> : null}
    </section>
  )
}

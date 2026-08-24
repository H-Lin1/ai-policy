import { useState, type FormEvent, type KeyboardEvent } from 'react'
import { Navigate, useLocation, useNavigate } from 'react-router-dom'

import { useAuth } from '../auth/AuthProvider'
import { authenticatedHomePath, roleWorkspacePath } from '../roleRoutes'

type LoginIntendedRole = 'individual' | 'enterprise' | 'government'

const publicRoleLabels: Record<LoginIntendedRole, string> = {
  individual: '个人服务',
  enterprise: '企业服务',
  government: '政府服务',
}

const publicRoleOrder: LoginIntendedRole[] = ['individual', 'enterprise', 'government']

export type PostLoginDecision =
  | { kind: 'default'; destination: typeof authenticatedHomePath }
  | { kind: 'matched'; destination: string }
  | { kind: 'mismatch'; actualRole: LoginIntendedRole | null; destination: string }

function readIntendedRole(state: unknown): LoginIntendedRole | null {
  if (!state || typeof state !== 'object' || !('intendedRole' in state)) return null
  const role = state.intendedRole
  return role === 'individual' || role === 'enterprise' || role === 'government' ? role : null
}

export function resolvePostLoginDecision(
  intendedRole: LoginIntendedRole | null,
  actualRoles: readonly string[],
): PostLoginDecision {
  if (!intendedRole) return { kind: 'default', destination: authenticatedHomePath }
  if (actualRoles.includes(intendedRole)) {
    return {
      kind: 'matched',
      destination: intendedRole === 'individual' || intendedRole === 'enterprise'
        ? authenticatedHomePath
        : roleWorkspacePath(intendedRole),
    }
  }
  const actualRole = publicRoleOrder.find((role) => actualRoles.includes(role)) ?? null
  return {
    kind: 'mismatch',
    actualRole,
    destination: actualRole === 'individual' || actualRole === 'enterprise'
      ? authenticatedHomePath
      : actualRole
        ? roleWorkspacePath(actualRole)
        : authenticatedHomePath,
  }
}

export function LoginPage() {
  const { state, signIn, signOut } = useAuth()
  const location = useLocation()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [busy, setBusy] = useState(false)
  const [switchingAccount, setSwitchingAccount] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const intendedRole = readIntendedRole(location.state)
  if (state.status === 'ready') {
    const decision = resolvePostLoginDecision(intendedRole, state.identity.roles)
    if (decision.kind !== 'mismatch') return <Navigate to={decision.destination} replace />
    return (
      <RoleMismatchDialog
        intendedRole={intendedRole as LoginIntendedRole}
        actualRole={decision.actualRole}
        switchingAccount={switchingAccount}
        onEnterActualService={() => navigate(decision.destination, { replace: true })}
        onSwitchAccount={() => {
          setEmail('')
          setPassword('')
          setError(null)
          setSwitchingAccount(true)
          void signOut().finally(() => setSwitchingAccount(false))
        }}
      />
    )
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setBusy(true)
    setError(null)
    try {
      setError(await signIn(email.trim(), password))
    } finally {
      setBusy(false)
    }
  }

  const unavailable = state.status === 'configuration_missing'
  return (
    <section className="page-content login-page">
      <div className="login-intro">
        <div className="eyebrow">政通惠 · 安全登录</div>
        <h1>进入你的<span className="accent-text">政策服务工作区</span></h1>
        <p className="lead">使用已配置的平台账号继续。身份和工作区权限由服务端统一核验。</p>
      </div>
      <div className="login-panel">
        <form className="login-form" onSubmit={submit}>
          <div className="login-form-heading">
            <span className="section-label">Account</span>
            <h2>账号登录</h2>
          </div>
          <label>
            <span>邮箱</span>
            <input
              type="email"
              autoComplete="username"
              placeholder="请输入邮箱"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              required
              disabled={busy || unavailable}
            />
          </label>
          <label>
            <span>密码</span>
            <input
              type="password"
              autoComplete="current-password"
              placeholder="请输入密码"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              required
              disabled={busy || unavailable}
            />
          </label>
          {unavailable ? <p className="error-message" role="status">{state.message}</p> : null}
          {error ? <p className="error-message" role="alert">{error}</p> : null}
          <button className="button button-primary" type="submit" disabled={busy || unavailable}>
            {busy ? '正在登录' : '登录'}
          </button>
        </form>
        <div className="login-assurance" aria-label="登录说明">
          <strong>深圳 · V1.0</strong>
          <span>登录后仅显示当前身份已获授权的服务入口。</span>
        </div>
      </div>
    </section>
  )
}

function RoleMismatchDialog({
  intendedRole,
  actualRole,
  switchingAccount,
  onEnterActualService,
  onSwitchAccount,
}: {
  intendedRole: LoginIntendedRole
  actualRole: LoginIntendedRole | null
  switchingAccount: boolean
  onEnterActualService: () => void
  onSwitchAccount: () => void
}) {
  const intendedLabel = publicRoleLabels[intendedRole]
  const actualLabel = actualRole ? publicRoleLabels[actualRole] : '其他已授权服务'
  function keepFocusInDialog(event: KeyboardEvent<HTMLDivElement>) {
    if (event.key !== 'Tab') return
    const buttons = Array.from(event.currentTarget.querySelectorAll<HTMLButtonElement>('button:not(:disabled)'))
    if (buttons.length === 0) return
    const first = buttons[0]
    const last = buttons[buttons.length - 1]
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault()
      last.focus()
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault()
      first.focus()
    }
  }
  return (
    <section className="role-mismatch-page" aria-label="登录角色确认">
      <div className="role-mismatch-dialog" role="dialog" aria-modal="true" aria-labelledby="role-mismatch-title" aria-describedby="role-mismatch-description" onKeyDown={keepFocusInDialog}>
        <span className="section-label">账号类型不匹配</span>
        <h1 id="role-mismatch-title">请选择正确的服务入口</h1>
        <p id="role-mismatch-description">
          当前选择的是<strong>{intendedLabel}</strong>，但登录账号属于<strong>{actualLabel}</strong>。系统不会自动切换工作区，请确认下一步。
        </p>
        <div className="role-mismatch-actions">
          <button className="button button-primary" type="button" autoFocus onClick={onEnterActualService} disabled={switchingAccount}>
            进入{actualLabel}
          </button>
          <button className="button button-secondary" type="button" onClick={onSwitchAccount} disabled={switchingAccount}>
            {switchingAccount ? '正在切换账号' : '切换' + intendedLabel + '账号'}
          </button>
        </div>
      </div>
    </section>
  )
}

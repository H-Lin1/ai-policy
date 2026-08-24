import { NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom'

import type { RoleCode } from '../lib/api/client'
import { useAuth } from './auth/AuthProvider'
import { authenticatedHomePath, roleWorkspacePath } from './roleRoutes'

const publicNavigation = [
  { to: '/', label: '首页', end: true },
  { to: '/policies', label: '政策中心' },
  { to: '/qa', label: '历史问答' },
  { to: '/classify', label: '智能分类' },
  { to: '/health', label: '服务状态' },
]

const roleNavigation: Array<{ role: RoleCode; to: string; label: string }> = [
  { role: 'individual', to: roleWorkspacePath('individual'), label: '个人服务' },
  { role: 'enterprise', to: roleWorkspacePath('enterprise'), label: '企业服务' },
  { role: 'government', to: roleWorkspacePath('government'), label: '政府办理' },
  { role: 'admin', to: roleWorkspacePath('admin'), label: '平台管理' },
]

const authenticatedUserNavigation = [
  { to: authenticatedHomePath, label: '首页' },
  { to: '/policies', label: '政策中心' },
  { to: '/qa', label: '历史问答' },
  { to: '/consultations', label: '政民互动' },
]

const authenticatedRoleNavigation = [
  { to: authenticatedHomePath, label: '首页' },
  ...publicNavigation.slice(1),
]

export function AppLayout() {
  const { state, hasSession, signOut } = useAuth()
  const location = useLocation()
  const navigate = useNavigate()
  const isPublicLanding = location.pathname === '/' && (
    state.status === 'loading'
    || state.status === 'configuration_missing'
    || state.status === 'signed_out'
  )
  const availableRoles = state.status === 'ready' ? state.identity.roles : []
  const isEnterpriseUser = availableRoles.includes('enterprise')
  const isIndividualUser = availableRoles.includes('individual') && !isEnterpriseUser
  const authenticatedNavigation = isEnterpriseUser || isIndividualUser
    ? [
        ...authenticatedUserNavigation,
        ...(isEnterpriseUser ? [{ to: '/my-enterprise', label: '我的企业' }] : []),
      ]
    : [
        ...authenticatedRoleNavigation,
        ...(availableRoles.includes('government') ? [{ to: '/consultations', label: '咨询办理' }] : []),
        ...roleNavigation.filter(({ role }) => availableRoles.includes(role)),
      ]
  const navigation = state.status === 'ready' ? authenticatedNavigation : publicNavigation
  const identityLabel = state.status === 'ready' ? state.identity.display_name : '未登录'
  const accountStatusClass = state.status === 'ready' ? 'is-ready' : 'is-idle'
  function handleSignOut() {
    void signOut()
    navigate('/', { replace: true })
  }

  return (
    <div className="app-shell">
      {!isPublicLanding ? <header className="site-header">
        <div className="site-header-inner">
          <div className="brand-row">
            <NavLink className="brand-lockup" to={state.status === 'ready' ? authenticatedHomePath : '/'} aria-label="政通惠首页">
              <span className="brand-name">政通惠</span>
              <span className="brand-caption">一站式政策服务平台</span>
            </NavLink>
            <span className="location-context" aria-label="当前地区：深圳">深圳</span>
          </div>
          <nav className="primary-nav" aria-label="主导航">
            {navigation.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === '/'}
                className={({ isActive }) => (isActive ? 'nav-item active' : 'nav-item')}
              >
                {item.label}
              </NavLink>
            ))}
          </nav>
          <div className={`account-panel ${accountStatusClass}`}>
            <span className="status-dot" aria-hidden="true" />
            <span className="account-label" title={identityLabel}>{identityLabel}</span>
            {hasSession ? (
              <button type="button" className="sign-out-button" onClick={handleSignOut}>
                退出登录
              </button>
            ) : (
              <NavLink className="account-login-link" to="/login">登录</NavLink>
            )}
          </div>
        </div>
      </header> : null}
      <main className="main-content">
        <Outlet />
      </main>
      <footer className="site-footer">
        <p>© 2026 政通惠 · 北京师范大学 靳健团队</p>
      </footer>
    </div>
  )
}

import type { ReactNode } from 'react'
import { Link, Navigate, useLocation } from 'react-router-dom'

import enterpriseServiceImage from '../../assets/ui1/enterprise-service.jpg'
import individualServiceImage from '../../assets/ui1/individual-service.jpg'
import type { RoleCode } from '../../lib/api/client'
import { useAuth } from '../auth/AuthProvider'
import { authenticatedHomePath, roleWorkspacePath } from '../roleRoutes'
import { PolicyQaWorkbench } from './PolicyQaWorkbench'

const roleEntries: Array<{ role: RoleCode; label: string; description: string }> = [
  { role: 'individual', label: '个人服务', description: '政策查询与个人办事服务' },
  { role: 'enterprise', label: '企业服务', description: '惠企政策与企业办事服务' },
  { role: 'government', label: '政府办理', description: '政策服务与事项办理工作区' },
  { role: 'admin', label: '平台管理', description: '平台配置与运行管理工作区' },
]

export function WorkspaceHomePage() {
  const { state, retry } = useAuth()
  const location = useLocation()
  const normalizedPath = location.pathname.replace(/\/+$/, '') || '/'
  const isAuthenticatedHome = normalizedPath === authenticatedHomePath
  if (state.status === 'ready' && !isAuthenticatedHome) {
    return <Navigate to={authenticatedHomePath} replace />
  }
  if ((state.status === 'signed_out' || state.status === 'configuration_missing') && isAuthenticatedHome) {
    return <Navigate to="/" replace />
  }
  if (state.status === 'loading') return <HomeState title="正在读取身份" />
  if (state.status === 'configuration_missing') {
    return <PublicLanding noticeTitle="登录服务未配置" noticeMessage={state.message} />
  }
  if (state.status === 'signed_out') {
    return <PublicLanding />
  }
  if (state.status === 'error') {
    return (
      <HomeState title="身份暂不可用" message={state.message}>
        <button className="button button-primary" type="button" onClick={retry}>重试</button>
      </HomeState>
    )
  }

  const qaEligible = state.identity.roles.some((role) => role === 'individual' || role === 'enterprise')
  if (qaEligible) {
    return <section className="workspace-home qa-home"><PolicyQaWorkbench compact variant="workspace" /></section>
  }

  const available = roleEntries.filter(({ role }) => state.identity.roles.includes(role))
  return <section className="page-content workspace-home non-qa-home">
    <div className="workspace-section-heading">
      <div>
        <span className="section-label">服务入口</span>
        <h1>你的工作区</h1>
      </div>
      <span className="scope-caption">{state.identity.region?.name ?? '深圳'}</span>
    </div>
    <div className="workspace-links" aria-label="可用工作区">
      {available.map(({ role, label, description }) => (
        <Link key={role} className={`workspace-link role-${role}`} to={roleWorkspacePath(role)}>
          <span className="workspace-link-index" aria-hidden="true">0{roleEntries.findIndex((entry) => entry.role === role) + 1}</span>
          <strong>{label}</strong>
          <span>{description}</span>
          <span className="workspace-link-action">进入工作区</span>
        </Link>
      ))}
    </div>
  </section>
}

function PublicLanding({
  noticeTitle,
  noticeMessage,
}: {
  noticeTitle?: string
  noticeMessage?: string
}) {
  return (
    <section className="page-content landing-page">
      <div className="landing-intro">
        <h1 className="landing-title">政通惠</h1>
        <p className="landing-subtitle">一站式政策服务平台</p>
      </div>
      {noticeTitle ? <div className="inline-notice" role="status">
        <strong>{noticeTitle}</strong>
        {noticeMessage ? <span>{noticeMessage}</span> : null}
      </div> : null}
      <div className="service-entry-grid" aria-label="服务入口">
        <ServiceEntry
          role="individual"
          image={individualServiceImage}
          imageAlt="个人服务"
          english="For Individuals"
          title="个人服务"
          description="面向个人的政策查询、政策解读与在线服务"
          action="进入个人版"
        />
        <ServiceEntry
          role="enterprise"
          image={enterpriseServiceImage}
          imageAlt="企业服务"
          english="For Enterprises"
          title="企业服务"
          description="面向企业的政策匹配、申报指导与专业服务"
          action="进入企业版"
        />
        <ServiceEntry
          role="government"
          image={enterpriseServiceImage}
          imageAlt="政府服务"
          english="For Government"
          title="政府服务"
          description="面向政府人员的政策服务、咨询办理与协同工作"
          action="进入政府版"
        />
      </div>
    </section>
  )
}

function ServiceEntry({
  role,
  image,
  imageAlt,
  english,
  title,
  description,
  action,
}: {
  role: 'individual' | 'enterprise' | 'government'
  image: string
  imageAlt: string
  english: string
  title: string
  description: string
  action: string
}) {
  return (
    <Link className={`service-entry service-entry-${role}`} to="/login" state={{ intendedRole: role }}>
      <img src={image} alt={imageAlt} />
      <span className="service-entry-overlay" aria-hidden="true" />
      <span className="service-entry-content">
        <span className="service-entry-english">{english}</span>
        <strong>{title}</strong>
        <span className="service-entry-description">{description}</span>
        <span className="service-entry-action">{action}<span aria-hidden="true"> →</span></span>
      </span>
    </Link>
  )
}

function HomeState({
  title,
  message,
  children,
}: {
  title: string
  message?: string
  children?: ReactNode
}) {
  return (
    <section className="page-content access-state state-page" aria-live="polite">
      <div className="eyebrow">政通惠 · 工作区</div>
      <h1>{title}</h1>
      {message ? <p className="lead">{message}</p> : null}
      {children ? <div className="state-actions">{children}</div> : null}
    </section>
  )
}

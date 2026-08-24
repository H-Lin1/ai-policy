import { useAuth } from '../auth/AuthProvider'
import { RoleGuard } from '../auth/RoleGuard'

export function EnterpriseProfilePage() {
  return (
    <RoleGuard role="enterprise">
      {() => <EnterpriseProfileContent />}
    </RoleGuard>
  )
}

export function EnterpriseProfileContent() {
  const { state } = useAuth()
  if (state.status !== 'ready') return null
  const { identity } = state
  const organization = identity.organization

  return (
    <section className="page-content enterprise-profile-page">
      <div className="workspace-hero">
        <div>
          <div className="eyebrow">政通惠 · 我的企业</div>
          <h1>{organization?.name ?? '企业信息'}</h1>
          <p className="lead">查看当前账号已授权的企业基本信息。</p>
        </div>
        <span className="role-badge">只读信息</span>
      </div>
      <section className="enterprise-profile-section" aria-labelledby="enterprise-profile-heading">
        <div className="workspace-section-heading">
          <div>
            <span className="section-label">Enterprise profile</span>
            <h2 id="enterprise-profile-heading">企业基本信息</h2>
          </div>
          <span className="scope-caption">{identity.display_name}</span>
        </div>
        <dl className="enterprise-info-grid">
          <InfoItem label="企业名称" value={organization?.name} />
          <InfoItem label="企业代码" value={organization?.code} />
          <InfoItem label="企业类型" value={organization?.organization_type} />
          <InfoItem label="所属地区" value={identity.region?.name} />
          <InfoItem label="当前账号" value={identity.display_name} />
          <InfoItem label="登录邮箱" value={identity.email} />
        </dl>
      </section>
    </section>
  )
}

function InfoItem({ label, value }: { label: string; value?: string | null }) {
  return (
    <div>
      <dt>{label}</dt>
      <dd>{value || '未设置'}</dd>
    </div>
  )
}

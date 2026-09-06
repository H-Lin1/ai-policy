import type { RoleCode, WorkspaceResponse } from '../../lib/api/client'
import { useAuth } from '../auth/AuthProvider'
import { RoleGuard } from '../auth/RoleGuard'
import { PolicyQaWorkbench } from './PolicyQaWorkbench'

const roleLabels: Record<RoleCode, string> = {
  individual: '个人服务',
  enterprise: '企业服务',
  government: '政府办理',
  admin: '管理员',
}

const roleDescriptions: Record<RoleCode, string> = {
  individual: '个人政策服务与办事支持',
  enterprise: '惠企政策服务与申报支持',
  government: '政府政策服务与办理工作区',
  admin: '管理员工作区',
}

export function RoleWorkspacePage({ role }: { role: RoleCode }) {
  return (
    <RoleGuard role={role}>
      {(workspace) => <WorkspaceContent workspace={workspace} />}
    </RoleGuard>
  )
}

function WorkspaceContent({ workspace }: { workspace: WorkspaceResponse }) {
  const { state } = useAuth()
  if (state.status !== 'ready') return null
  const { identity } = state
  const roleName = identity.role_summaries.find((item) => item.code === workspace.role)?.name

  return (
    <section className={`page-content role-workspace role-${workspace.role}`}>
      <div className="workspace-hero">
        <div>
          <div className="eyebrow">政通惠 · {roleLabels[workspace.role]}</div>
          <h1>{workspace.title}</h1>
          <p className="lead">{roleDescriptions[workspace.role]}</p>
        </div>
        <span className="role-badge">{roleName ?? workspace.role}</span>
      </div>
      {workspace.role === 'individual' || workspace.role === 'enterprise' ? <PolicyQaWorkbench variant="workspace" /> : null}
      <div className="workspace-scope-section">
        <div className="workspace-section-heading">
          <div>
            <span className="section-label">Authorized scope</span>
            <h2>当前身份范围</h2>
          </div>
          <span className="scope-caption">{identity.display_name}</span>
        </div>
        <dl className="scope-grid">
          <div>
            <dt>身份</dt>
            <dd>{identity.email ?? identity.display_name}</dd>
          </div>
          <div>
            <dt>地区</dt>
            <dd>{workspace.region?.name ?? '未设置'}</dd>
          </div>
          <div>
            <dt>组织</dt>
            <dd>{workspace.organization?.name ?? '个人身份'}</dd>
          </div>
        </dl>
      </div>
    </section>
  )
}

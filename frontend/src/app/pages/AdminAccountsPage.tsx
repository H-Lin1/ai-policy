import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import { ApiError, apiClient, type AdminAccountSummary, type RoleCode } from '../../lib/api/client'
import { useAuth } from '../auth/AuthProvider'

const roleLabels: Record<RoleCode, string> = { individual: '个人', enterprise: '企业', government: '政府', admin: '管理员' }

export function AdminAccountsPage() {
  const { state, getAccessToken } = useAuth()
  const [items, setItems] = useState<AdminAccountSummary[]>([])
  const [role, setRole] = useState(''); const [status, setStatus] = useState(''); const [keyword, setKeyword] = useState('')
  const [error, setError] = useState<string | null>(null); const [loading, setLoading] = useState(true)
  function load() { if (state.status !== 'ready' || !state.identity.roles.includes('admin')) return; const token = getAccessToken(); if (!token) return; setLoading(true); void apiClient.getAdminAccounts({ role, status, keyword }, token).then((page) => setItems(page.items)).catch((cause) => setError(cause instanceof ApiError ? cause.message : '账号列表暂不可用。')).finally(() => setLoading(false)) }
  useEffect(load, [getAccessToken, keyword, role, state, status])
  if (state.status !== 'ready' || !state.identity.roles.includes('admin')) return <section className="page-content empty-state"><h1>无权访问</h1></section>
  async function toggle(item: AdminAccountSummary) { if (!window.confirm(`确认${item.status === 'active' ? '停用' : '恢复'}账号 ${item.username} 吗？`)) return; const token = getAccessToken(); if (!token) return; try { item.status === 'active' ? await apiClient.disableAdminAccount(item.user_id, token) : await apiClient.enableAdminAccount(item.user_id, token); load() } catch (cause) { setError(cause instanceof ApiError ? cause.message : '账号状态修改失败。') } }
  return <section className="page-content account-management-page"><div className="admin-policy-heading"><div><div className="eyebrow">Account management</div><h1>账号管理</h1><p className="lead">查看和维护个人、企业、政府与管理员账号。</p></div><Link className="button button-primary" to="/account-management/new">新增账号</Link></div><div className="account-filters"><select aria-label="角色筛选" value={role} onChange={(e) => setRole(e.target.value)}><option value="">全部角色</option>{Object.entries(roleLabels).map(([code, label]) => <option key={code} value={code}>{label}</option>)}</select><select aria-label="状态筛选" value={status} onChange={(e) => setStatus(e.target.value)}><option value="">全部状态</option><option value="active">正常</option><option value="disabled">已停用</option></select><input aria-label="搜索账号" placeholder="搜索账号、姓名、组织或部门" value={keyword} onChange={(e) => setKeyword(e.target.value)} /></div>{error ? <p className="error-message">{error}</p> : null}{loading ? <p className="muted">正在读取账号…</p> : <div className="account-list">{items.map((item) => <article className="account-card" key={item.user_id}><div><span className={`policy-status policy-status-${item.status === 'active' ? 'published' : 'withdrawn'}`}>{item.status === 'active' ? '正常' : '已停用'}</span><h2>{item.display_name}</h2><p>{item.username} · {item.roles.map((value) => roleLabels[value]).join('、')}</p><p>{item.department_name ?? item.organization_name ?? '个人身份'}</p></div><div className="admin-policy-actions"><Link className="button button-secondary" to={`/account-management/${item.user_id}`}>查看编辑</Link><button className="button button-secondary" onClick={() => void toggle(item)}>{item.status === 'active' ? '停用' : '恢复'}</button></div></article>)}</div>}</section>
}

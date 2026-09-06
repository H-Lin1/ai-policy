import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { ApiError, apiClient, type AdminApplicationSummary } from '../../lib/api/client'
import { useAuth } from '../auth/AuthProvider'

export function AdminRegistrationApplicationsPage() {
  const { state, getAccessToken } = useAuth(); const [items, setItems] = useState<AdminApplicationSummary[]>([]); const [error, setError] = useState<string | null>(null)
  useEffect(() => { if (state.status !== 'ready') return; const token = getAccessToken(); if (!token || !state.identity.roles.includes('admin')) return; void apiClient.getAdminRegistrationApplications({ status: 'pending' }, token).then((page) => setItems(page.items)).catch((cause) => setError(cause instanceof ApiError ? cause.message : '申请列表暂不可用。')) }, [getAccessToken, state])
  if (state.status !== 'ready') return <section className="page-content empty-state"><h1>需要登录</h1><p>请使用管理员账号登录。</p></section>
  if (!state.identity.roles.includes('admin')) return <section className="page-content empty-state"><h1>无权访问</h1><p>只有管理员可以处理注册申请。</p></section>
  return <section className="page-content admin-applications-page"><div className="eyebrow">Admin review</div><h1>注册申请管理</h1>{error ? <p className="error-message" role="alert">{error}</p> : null}{!items.length && !error ? <p className="muted">暂无待审核申请。</p> : <div className="admin-application-list">{items.map((item) => <Link className="admin-application-item" key={item.id} to={`/registration-applications/${item.id}`}><strong>{item.title}</strong><span>{item.application_type === 'enterprise' ? '企业申请' : '政府申请'} · {item.user_name}</span><small>{new Date(item.submitted_at).toLocaleString('zh-CN')}</small></Link>)}</div>}</section>
}

import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import { ApiError, apiClient, type AdminPolicyRecord, type AdminPolicyStatus } from '../../lib/api/client'
import { useAuth } from '../auth/AuthProvider'

const statusLabels: Record<AdminPolicyStatus, string> = { draft: '草稿', published: '已发布', withdrawn: '已撤回' }

export function AdminPoliciesPage() {
  const { state, getAccessToken } = useAuth()
  const [filter, setFilter] = useState<AdminPolicyStatus | ''>('')
  const [items, setItems] = useState<AdminPolicyRecord[]>([])
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  function load() {
    if (state.status !== 'ready' || !state.identity.roles.includes('admin')) return
    const token = getAccessToken()
    if (!token) return
    setLoading(true); setError(null)
    void apiClient.getAdminPolicies(filter, token).then(setItems).catch((cause) => setError(cause instanceof ApiError ? cause.message : '政策管理暂不可用。')).finally(() => setLoading(false))
  }
  useEffect(load, [filter, getAccessToken, state])

  if (state.status !== 'ready' || !state.identity.roles.includes('admin')) return <section className="page-content empty-state"><h1>无权访问</h1><p>只有管理员可以管理政策。</p></section>
  async function withdraw(item: AdminPolicyRecord) {
    const reason = window.prompt('请输入撤回原因', '')
    if (!reason?.trim()) return
    const token = getAccessToken(); if (!token) return
    try { await apiClient.withdrawAdminPolicy(item.id, reason, token); load() } catch (cause) { setError(cause instanceof ApiError ? cause.message : '撤回失败。') }
  }
  async function publish(item: AdminPolicyRecord) {
    const token = getAccessToken(); if (!token) return
    try { await apiClient.publishAdminPolicy(item.id, token); load() } catch (cause) { setError(cause instanceof ApiError ? cause.message : '发布失败。') }
  }
  return <section className="page-content admin-policies-page"><div className="admin-policy-heading"><div><div className="eyebrow">Policy administration</div><h1>政策管理</h1><p className="lead">手工录入或批量导入 Markdown，核对后保存草稿或发布。</p></div><Link className="button button-primary" to="/policy-management/new">新增或导入政策</Link></div><div className="admin-policy-filters" aria-label="政策状态筛选">{(['', 'draft', 'published', 'withdrawn'] as const).map((value) => <button key={value || 'all'} className={`button ${filter === value ? 'button-primary' : 'button-secondary'}`} onClick={() => setFilter(value)}>{value ? statusLabels[value] : '全部'}</button>)}</div>{error ? <p className="error-message" role="alert">{error}</p> : null}{loading ? <p className="muted">正在读取政策…</p> : !items.length ? <p className="muted">当前没有政策记录。</p> : <div className="admin-policy-list">{items.map((item) => <article className="admin-policy-card" key={item.id}><div><span className={`policy-status policy-status-${item.publication_status}`}>{statusLabels[item.publication_status]}</span><h2>{item.title}</h2><p>{item.issuing_organization} · {item.published_date}</p></div><div className="admin-policy-actions">{item.publication_status === 'draft' ? <button className="button button-primary" onClick={() => void publish(item)}>发布</button> : null}{item.publication_status === 'published' ? <button className="button button-secondary" onClick={() => void withdraw(item)}>撤回</button> : null}</div></article>)}</div>}</section>
}

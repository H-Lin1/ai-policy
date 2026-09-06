import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'

import { useAuth } from '../auth/AuthProvider'
import { ApiError, apiClient, type PageResponse, type PolicyDetail, type PolicyListItem } from '../../lib/api/client'

type LoadState =
  | { status: 'loading' }
  | { status: 'ready'; page: PageResponse<PolicyListItem> }
  | { status: 'detail'; policy: PolicyDetail }
  | { status: 'error'; message: string }

export function PolicyWorkspacePage() {
  return <PolicyContent />
}

function PolicyContent() {
  const { policyId } = useParams<{ policyId?: string }>()
  const { state, getAccessToken } = useAuth()
  const [page, setPage] = useState(1)
  const [loadState, setLoadState] = useState<LoadState>({ status: 'loading' })
  const token = state.status === 'ready' ? getAccessToken() : null

  useEffect(() => {
    let active = true
    if (!token) {
      setLoadState({ status: 'error', message: '登录后可查看政策全文。' })
      return () => { active = false }
    }
    setLoadState({ status: 'loading' })
    const request = policyId
      ? apiClient.getPolicy(policyId, token)
      : apiClient.getPolicies({ page, pageSize: 10 }, token)
    void request
      .then((result) => {
        if (!active) return
        setLoadState(policyId ? { status: 'detail', policy: result as PolicyDetail } : { status: 'ready', page: result as PageResponse<PolicyListItem> })
      })
      .catch((error: unknown) => {
        if (!active) return
        const message = error instanceof ApiError ? error.message : '政策服务暂不可用。'
        setLoadState({ status: 'error', message })
      })
    return () => { active = false }
  }, [page, policyId, token])

  if (state.status !== 'ready' || !token) {
    return <PolicyState title="需要登录" message="登录后可查看已核验的政策内容。" />
  }
  if (loadState.status === 'loading') {
    return <PolicyState title={policyId ? '正在读取政策' : '正在读取政策列表'} message="正在从政策服务读取内容。" pending />
  }
  if (loadState.status === 'error') {
    return <PolicyState title="政策服务暂不可用" message={loadState.message} />
  }
  if (loadState.status === 'detail') {
    return <PolicyDetailView policy={loadState.policy} />
  }
  if (loadState.page.items.length === 0) {
    return <PolicyState title="暂无政策记录" message="当前筛选范围内没有可展示的政策内容。" />
  }
  return <PolicyListView page={loadState.page} onPageChange={setPage} />
}

export function PolicyListView({ page, onPageChange }: { page: PageResponse<PolicyListItem>; onPageChange: (page: number) => void }) {
  return (
    <section className="page-content policy-page">
      <div className="eyebrow">政策中心</div>
      <h1>政策库</h1>
      <p className="lead">来自政府公开渠道的政策原文与来源信息。</p>
      <div className="policy-list" aria-live="polite">
        {page.items.map((policy) => <PolicyListCard key={policy.id} policy={policy} />)}
      </div>
      <div className="policy-pagination" aria-label="政策分页">
        <button className="button button-secondary" type="button" disabled={!page.meta.has_previous} onClick={() => onPageChange(page.meta.page - 1)}>上一页</button>
        <span>第 {page.meta.page} / {Math.max(page.meta.total_pages, 1)} 页</span>
        <button className="button button-secondary" type="button" disabled={!page.meta.has_next} onClick={() => onPageChange(page.meta.page + 1)}>下一页</button>
      </div>
    </section>
  )
}

function PolicyListCard({ policy }: { policy: PolicyListItem }) {
  return (
    <article className="policy-card">
      <div className="policy-card-meta">{policy.issuing_organization ?? '发布机构待补充'}{policy.published_date ? ` · ${policy.published_date}` : ''}</div>
      <h2><Link to={`/policies/${policy.id}`}>{policy.title}</Link></h2>
      <p>{policy.document_no ?? '官方文号待补充'}</p>
      {policy.source_url ? <a href={policy.source_url} target="_blank" rel="noreferrer">查看官方来源</a> : null}
    </article>
  )
}

export function PolicyDetailView({ policy }: { policy: PolicyDetail }) {
  return (
    <article className="page-content policy-detail">
      <Link className="policy-back-link" to="/policies">返回政策库</Link>
      <div className="eyebrow">政策详情</div>
      <h1>{policy.title}</h1>
      <dl className="policy-facts">
        <div><dt>发布机构</dt><dd>{policy.issuing_organization ?? '待补充'}</dd></div>
        <div><dt>发布日期</dt><dd>{policy.published_date ?? '待补充'}</dd></div>
        <div><dt>官方文号</dt><dd>{policy.document_no ?? '待补充'}</dd></div>
        <div><dt>采集时间</dt><dd>{new Date(policy.collected_at).toLocaleString('zh-CN')}</dd></div>
      </dl>
      {policy.document_url ?? policy.source_url ? <p><a href={policy.document_url ?? policy.source_url ?? undefined} target="_blank" rel="noreferrer">查看官方原文</a></p> : null}
      <div className="policy-content-text">{policy.content_text.split('\n').map((paragraph, index) => <p key={`${index}-${paragraph.slice(0, 12)}`}>{paragraph || '\u00a0'}</p>)}</div>
    </article>
  )
}

function PolicyState({ title, message, pending = false }: { title: string; message: string; pending?: boolean }) {
  return <section className="page-content policy-state" aria-live="polite" aria-busy={pending}><div className="eyebrow">政策中心</div><h1>{title}</h1><p className="lead">{message}</p></section>
}

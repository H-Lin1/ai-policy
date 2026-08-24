import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'

import { useAuth } from '../auth/AuthProvider'
import { ApiError, apiClient, type HistoricalQaDetail, type HistoricalQaListItem, type PageResponse } from '../../lib/api/client'

type LoadState =
  | { status: 'loading' }
  | { status: 'ready'; page: PageResponse<HistoricalQaListItem> }
  | { status: 'detail'; record: HistoricalQaDetail }
  | { status: 'error'; message: string }

export function HistoricalQaWorkspacePage() {
  const { qaId } = useParams<{ qaId?: string }>()
  const { state, getAccessToken } = useAuth()
  const [page, setPage] = useState(1)
  const [loadState, setLoadState] = useState<LoadState>({ status: 'loading' })
  const token = state.status === 'ready' ? getAccessToken() : null

  useEffect(() => {
    let active = true
    if (!token) {
      setLoadState({ status: 'error', message: '登录后可查看历史政务问答。' })
      return () => { active = false }
    }
    setLoadState({ status: 'loading' })
    const request = qaId ? apiClient.getHistoricalQaDetail(qaId, token) : apiClient.getHistoricalQa({ page, pageSize: 10 }, token)
    void request.then((result) => {
      if (!active) return
      setLoadState(qaId ? { status: 'detail', record: result as HistoricalQaDetail } : { status: 'ready', page: result as PageResponse<HistoricalQaListItem> })
    }).catch((error: unknown) => {
      if (!active) return
      setLoadState({ status: 'error', message: error instanceof ApiError ? error.message : '历史问答服务暂不可用。' })
    })
    return () => { active = false }
  }, [page, qaId, token])

  if (state.status !== 'ready' || !token) return <QaState title="需要登录" message="登录后可查看经隐私筛选的历史问答。" />
  if (loadState.status === 'loading') return <QaState title={qaId ? '正在读取问答' : '正在读取问答列表'} message="正在从政务问答服务读取内容。" pending />
  if (loadState.status === 'error') return <QaState title="历史问答暂不可用" message={loadState.message} />
  if (loadState.status === 'detail') return <HistoricalQaDetailView record={loadState.record} />
  if (!loadState.page.items.length) return <QaState title="暂无历史问答" message="当前筛选范围内没有可展示的问答内容。" />
  return <HistoricalQaListView page={loadState.page} onPageChange={setPage} />
}

export function HistoricalQaListView({ page, onPageChange }: { page: PageResponse<HistoricalQaListItem>; onPageChange: (page: number) => void }) {
  return <section className="page-content qa-page"><div className="eyebrow">政务问答</div><h1>历史问答</h1><p className="lead">来自政府公开渠道，并经自动隐私筛选的历史答复。</p>
    <div className="qa-list" aria-live="polite">{page.items.map((item) => <article className="qa-card" key={item.id}><div className="policy-card-meta">{item.publishing_organization} {item.replied_at ? `· ${new Date(item.replied_at).toLocaleDateString('zh-CN')}` : ''}</div><h2><Link to={`/qa/${item.id}`}>{item.topic}</Link></h2><p>{item.contains_legal_basis ? '含已识别的法律依据' : '未标注法律依据'}</p><a href={item.source_url} target="_blank" rel="noreferrer">查看官方来源</a></article>)}</div>
    <div className="policy-pagination" aria-label="历史问答分页"><button className="button button-secondary" type="button" disabled={!page.meta.has_previous} onClick={() => onPageChange(page.meta.page - 1)}>上一页</button><span>第 {page.meta.page} / {Math.max(page.meta.total_pages, 1)} 页</span><button className="button button-secondary" type="button" disabled={!page.meta.has_next} onClick={() => onPageChange(page.meta.page + 1)}>下一页</button></div>
  </section>
}

export function HistoricalQaDetailView({ record }: { record: HistoricalQaDetail }) {
  return <article className="page-content policy-detail qa-detail"><Link className="policy-back-link" to="/qa">返回历史问答</Link><div className="eyebrow">政务问答详情</div><h1>{record.topic}</h1>
    <dl className="policy-facts"><div><dt>发布机构</dt><dd>{record.publishing_organization}</dd></div><div><dt>答复时间</dt><dd>{record.replied_at ? new Date(record.replied_at).toLocaleString('zh-CN') : '待补充'}</dd></div><div><dt>留言时间</dt><dd>{record.question_at ? new Date(record.question_at).toLocaleString('zh-CN') : '待补充'}</dd></div><div><dt>法律依据</dt><dd>{record.legal_basis_name ?? '未标注'}</dd></div></dl>
    <p><a href={record.source_url} target="_blank" rel="noreferrer">查看官方来源</a></p><section className="qa-text-section"><h2>群众留言</h2><QaText value={record.question_text} /></section><section className="qa-text-section"><h2>政府答复</h2><QaText value={record.answer_text} /></section>{record.legal_basis_citation ? <section className="qa-text-section"><h2>法律依据引文</h2><QaText value={record.legal_basis_citation} /></section> : null}
  </article>
}

function QaText({ value }: { value: string }) { return <div className="policy-content-text">{value.split('\n').map((paragraph, index) => <p key={`${index}-${paragraph.slice(0, 12)}`}>{paragraph || '\u00a0'}</p>)}</div> }
function QaState({ title, message, pending = false }: { title: string; message: string; pending?: boolean }) { return <section className="page-content policy-state" aria-live="polite" aria-busy={pending}><div className="eyebrow">政务问答</div><h1>{title}</h1><p className="lead">{message}</p></section> }

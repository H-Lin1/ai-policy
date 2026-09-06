import { useState, type ChangeEvent, type FormEvent } from 'react'
import { Link } from 'react-router-dom'

import { ApiError, apiClient, type AdminPolicyInput, type MarkdownParseItem, type PolicyEffectiveStatus } from '../../lib/api/client'
import { useAuth } from '../auth/AuthProvider'

const emptyPolicy: AdminPolicyInput = { title: '', document_no: '', issuing_organization: '', source_url: '', document_url: '', published_date: '', effective_status: 'unknown', content_text: '', source_type: 'manual' }

export function AdminPolicyEditorPage() {
  const { state, getAccessToken } = useAuth()
  const [mode, setMode] = useState<'manual' | 'markdown'>('manual')
  const [manual, setManual] = useState<AdminPolicyInput>(emptyPolicy)
  const [items, setItems] = useState<MarkdownParseItem[]>([])
  const [selected, setSelected] = useState<Set<number>>(new Set())
  const [preview, setPreview] = useState<AdminPolicyInput | null>(null)
  const [busy, setBusy] = useState(false)
  const [message, setMessage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  if (state.status !== 'ready' || !state.identity.roles.includes('admin')) return <section className="page-content empty-state"><h1>无权访问</h1></section>
  const token = getAccessToken()
  function updateItem(index: number, key: keyof AdminPolicyInput, value: string) { setItems((current) => current.map((item, itemIndex) => itemIndex === index && item.fields ? { ...item, fields: { ...item.fields, [key]: value }, status: item.status === 'failed' ? 'failed' : 'ready' } : item)) }
  async function readFiles(event: ChangeEvent<HTMLInputElement>) {
    await parseFiles(Array.from(event.target.files ?? []))
  }
  async function parseFiles(files: File[]) {
    if (!token || !files.length) return
    if (files.length > 20) { setError('单批最多选择 20 个 Markdown 文件。'); return }
    setBusy(true); setError(null); setMessage(null)
    try {
      const payload = await Promise.all(files.map(async (file) => ({ filename: file.name, content: await file.text() })))
      const result = await apiClient.parsePolicyMarkdown(payload, token)
      setItems(result.items); setSelected(new Set(result.items.map((item, index) => item.status !== 'failed' ? index : -1).filter((index) => index >= 0)))
    } catch (cause) { setError(cause instanceof ApiError ? cause.message : 'Markdown 解析失败。') } finally { setBusy(false) }
  }
  async function downloadExample() {
    if (!token) return
    try { const content = await apiClient.getPolicyMarkdownExample(token); const url = URL.createObjectURL(new Blob([content], { type: 'text/markdown;charset=utf-8' })); const anchor = document.createElement('a'); anchor.href = url; anchor.download = 'policy-example.md'; anchor.click(); URL.revokeObjectURL(url) } catch (cause) { setError(cause instanceof ApiError ? cause.message : '示例下载失败。') }
  }
  async function saveOne(fields: AdminPolicyInput, action: 'draft' | 'publish') { if (!token) throw new Error('missing token'); return apiClient.createAdminPolicy({ ...fields, action }, token) }
  async function submitManual(event: FormEvent, action: 'draft' | 'publish') { event.preventDefault(); setBusy(true); setError(null); try { const saved = await saveOne(manual, action); setMessage(`${saved.title}已${action === 'publish' ? '发布' : '保存为草稿'}。`) } catch (cause) { setError(cause instanceof ApiError ? cause.message : '政策保存失败。') } finally { setBusy(false) } }
  async function saveSelected(action: 'draft' | 'publish') {
    const targets = items.map((item, index) => ({ item, index })).filter(({ item, index }) => selected.has(index) && item.fields && item.status !== 'failed')
    if (!targets.length) { setError('请先选择至少一条可用政策。'); return }
    if (action === 'publish' && !window.confirm(`确认发布选中的 ${targets.length} 条政策吗？`)) return
    setBusy(true); setError(null); let success = 0; const failures: string[] = []
    for (const { item } of targets) { try { await saveOne(item.fields!, action); success += 1 } catch (cause) { failures.push(`${item.filename}：${cause instanceof ApiError ? cause.message : '保存失败'}`) } }
    setMessage(`处理完成：成功 ${success} 条，失败 ${failures.length} 条。`); setError(failures.length ? failures.join('；') : null); setBusy(false)
  }
  return <section className="page-content admin-policy-editor"><Link className="policy-back-link" to="/policy-management">返回政策管理</Link><div className="eyebrow">Policy authoring</div><h1>新增或导入政策</h1><div className="admin-policy-mode"><button className={`button ${mode === 'manual' ? 'button-primary' : 'button-secondary'}`} onClick={() => setMode('manual')}>手工录入</button><button className={`button ${mode === 'markdown' ? 'button-primary' : 'button-secondary'}`} onClick={() => setMode('markdown')}>批量 Markdown</button></div>{mode === 'manual' ? <form className="admin-policy-form" onSubmit={(event) => void submitManual(event, 'draft')}><PolicyFields value={manual} onChange={(key, value) => setManual((current) => ({ ...current, [key]: value }))} /> <div className="admin-policy-actions"><button className="button button-secondary" type="button" onClick={() => setPreview(manual)}>预览</button><button className="button button-secondary" type="submit" disabled={busy}>保存草稿</button><button className="button button-primary" type="button" disabled={busy} onClick={(event) => { if (window.confirm('确认发布这条政策吗？')) void submitManual(event as unknown as FormEvent, 'publish') }}>确认发布</button></div></form> : <div className="markdown-batch-panel"><div className="markdown-upload-box" onDragOver={(event) => event.preventDefault()} onDrop={(event) => { event.preventDefault(); void parseFiles(Array.from(event.dataTransfer.files)) }}><input type="file" accept=".md,text/markdown,text/plain" multiple onChange={(event) => void readFiles(event)} disabled={busy} /><p>选择或拖入文件：一次最多 20 个 Markdown；单文件最大 2 MB；不限制整批总大小。</p><button className="text-link markdown-example-button" type="button" onClick={() => void downloadExample()}>下载 Markdown 示例</button></div><div className="markdown-item-list">{items.map((item, index) => <article className={`markdown-item markdown-item-${item.status}`} key={`${item.filename}-${index}`}><div className="markdown-item-heading"><label><input type="checkbox" disabled={!item.fields || item.status === 'failed'} checked={selected.has(index)} onChange={(event) => setSelected((current) => { const next = new Set(current); event.target.checked ? next.add(index) : next.delete(index); return next })} /> {item.filename}</label><span>{item.status === 'failed' ? '解析失败' : item.status === 'warning' ? '存在提示' : '可处理'}</span></div>{item.errors.map((value) => <p className="error-message" key={value}>{value}</p>)}{item.warnings.map((value) => <p className="muted" key={value}>{value}</p>)}{item.fields ? <><PolicyFields compact value={item.fields} onChange={(key, value) => updateItem(index, key, value)} /><button className="button button-secondary" onClick={() => setPreview(item.fields ?? null)}>预览</button></> : null}</article>)}</div>{items.length ? <div className="admin-policy-actions"><button className="button button-secondary" disabled={busy} onClick={() => void saveSelected('draft')}>批量保存草稿</button><button className="button button-primary" disabled={busy} onClick={() => void saveSelected('publish')}>批量确认发布</button></div> : null}</div>}{message ? <p className="success-message" role="status">{message}</p> : null}{error ? <p className="error-message" role="alert">{error}</p> : null}{preview ? <PolicyPreview policy={preview} onClose={() => setPreview(null)} /> : null}</section>
}

function PolicyFields({ value, onChange, compact = false }: { value: AdminPolicyInput; onChange: (key: keyof AdminPolicyInput, value: string) => void; compact?: boolean }) {
  return <div className={`policy-fields ${compact ? 'is-compact' : ''}`}><label><span>政策标题</span><input required value={value.title} onChange={(e) => onChange('title', e.target.value)} /></label><label><span>发文字号</span><input value={value.document_no ?? ''} onChange={(e) => onChange('document_no', e.target.value)} /></label><label><span>发布机构</span><input required value={value.issuing_organization} onChange={(e) => onChange('issuing_organization', e.target.value)} /></label><label><span>发布日期</span><input required type="date" value={value.published_date} onChange={(e) => onChange('published_date', e.target.value)} /></label><label><span>政策状态</span><select value={value.effective_status} onChange={(e) => onChange('effective_status', e.target.value as PolicyEffectiveStatus)}><option value="active">现行有效</option><option value="pending">尚未生效</option><option value="expired">已失效</option><option value="repealed">已废止</option><option value="unknown">状态未知</option></select></label><label><span>来源网址</span><input type="url" value={value.source_url ?? ''} onChange={(e) => onChange('source_url', e.target.value)} /></label><label><span>正式文件网址</span><input type="url" value={value.document_url ?? ''} onChange={(e) => onChange('document_url', e.target.value)} /></label><label className="policy-body-field"><span>政策正文</span><textarea required value={value.content_text} onChange={(e) => onChange('content_text', e.target.value)} /></label></div>
}

function PolicyPreview({ policy, onClose }: { policy: AdminPolicyInput; onClose: () => void }) {
  return <div className="approval-dialog-backdrop"><div className="policy-preview-dialog" role="dialog" aria-modal="true" aria-labelledby="policy-preview-title"><button className="policy-preview-close" onClick={onClose} aria-label="关闭预览">×</button><div className="eyebrow">政策预览</div><h2 id="policy-preview-title">{policy.title || '未填写标题'}</h2><p>{policy.issuing_organization || '发布机构待补充'} · {policy.published_date || '发布日期待补充'}</p><div className="policy-preview-content">{policy.content_text || '政策正文待补充'}</div></div></div>
}

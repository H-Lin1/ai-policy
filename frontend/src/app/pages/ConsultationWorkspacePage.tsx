import { useEffect, useMemo, useState } from 'react'
import { useLocation } from 'react-router-dom'

import { ApiError, apiClient, type ConsultationDepartment, type ConsultationPrediction, type ConsultationRecord } from '../../lib/api/client'
import { useAuth } from '../auth/AuthProvider'

type FormState = 'idle' | 'classifying' | 'submitting' | 'success' | 'error'

export function ConsultationWorkspacePage() {
  const { state } = useAuth()
  if (state.status !== 'ready') return <ConsultationState title="需要登录" message="登录个人、企业或政府部门账号后可使用咨询服务。" />
  return state.identity.roles.includes('government') && !state.identity.roles.some((role) => role === 'individual' || role === 'enterprise')
    ? <GovernmentConsultations />
    : <RequesterConsultations />
}

function RequesterConsultations() {
  const { getAccessToken } = useAuth()
  const location = useLocation()
  const token = getAccessToken() ?? ''
  const draft = useMemo(() => new URLSearchParams(location.search).get('draft') ?? '', [location.search])
  const [question, setQuestion] = useState(draft)
  const [departments, setDepartments] = useState<ConsultationDepartment[]>([])
  const [recommendations, setRecommendations] = useState<ConsultationPrediction[]>([])
  const [selectedDepartmentId, setSelectedDepartmentId] = useState('')
  const [formState, setFormState] = useState<FormState>('idle')
  const [message, setMessage] = useState('')
  const [created, setCreated] = useState<ConsultationRecord | null>(null)
  const [records, setRecords] = useState<ConsultationRecord[]>([])

  useEffect(() => {
    let active = true
    void Promise.all([apiClient.getConsultationDepartments(token), apiClient.getConsultations(token)]).then(([directory, consultations]) => {
      if (!active) return
      setDepartments(directory)
      setRecords(consultations)
    }).catch((error: unknown) => active && setMessage(error instanceof ApiError ? error.message : '咨询服务暂不可用。'))
    return () => { active = false }
  }, [token])

  async function classify() {
    if (!question.trim()) return
    setFormState('classifying'); setMessage('')
    try {
      const result = await apiClient.classify(question.trim(), token)
      const topThree = result.predictions.slice(0, 3)
      setRecommendations(topThree)
      setSelectedDepartmentId((current) => current || topThree[0]?.department_id || '')
      setFormState('idle')
    } catch (error) {
      setFormState('error'); setMessage(error instanceof ApiError ? error.message : '智能分类暂不可用。')
    }
  }

  async function submit(event: React.FormEvent) {
    event.preventDefault()
    if (!question.trim() || !selectedDepartmentId) return
    setFormState('submitting'); setMessage('')
    try {
      const result = await apiClient.createConsultation({ question: question.trim(), selectedDepartmentId }, token)
      setCreated(result); setRecords((current) => [result, ...current]); setFormState('success')
    } catch (error) {
      setFormState('error'); setMessage(error instanceof ApiError ? error.message : '咨询提交失败。')
    }
  }

  return <section className="page-content consultation-page"><div className="eyebrow">政民互动</div><h1>政民互动</h1><p className="lead">向政府部门提交咨询工单，并在下方查看每一条咨询的办理状态与答复。</p>
    <section className="consultation-submit-section" aria-labelledby="consultation-submit-title"><div className="consultation-section-heading"><div><span className="section-label">提交工单</span><h2 id="consultation-submit-title">向政府部门提交咨询工单</h2></div><p>系统先给出前三个部门建议；最终由您从完整的 35 个部门目录中选择，提交后会立即自动派单。</p></div>
    <form className="consultation-form" onSubmit={submit}><label htmlFor="consultation-question">咨询内容</label><textarea id="consultation-question" value={question} onChange={(event) => setQuestion(event.target.value)} maxLength={4000} placeholder="请描述您需要咨询的事项…" />
      <div className="consultation-form-actions"><span>{question.trim().length} / 4000</span><button className="button button-secondary" type="button" disabled={!question.trim() || formState === 'classifying'} onClick={() => void classify()}>{formState === 'classifying' ? '正在推荐…' : '获取部门推荐'}</button></div>
      {recommendations.length ? <section className="recommendation-panel" aria-live="polite"><h2>推荐部门（仅供选择参考）</h2><div className="recommendation-list">{recommendations.map((item, index) => <button type="button" className={selectedDepartmentId === item.department_id ? 'recommendation selected' : 'recommendation'} key={item.department_id} onClick={() => setSelectedDepartmentId(item.department_id)}><span>推荐 {index + 1}</span><strong>{item.department_name}</strong><em>{(item.confidence * 100).toFixed(1)}%</em></button>)}</div></section> : null}
      <label htmlFor="consultation-department">最终办理部门</label><select id="consultation-department" value={selectedDepartmentId} onChange={(event) => setSelectedDepartmentId(event.target.value)} required><option value="">请选择部门</option>{departments.map((department) => <option key={department.department_id} value={department.department_id}>{department.department_name}</option>)}</select>
      <button className="button button-primary" type="submit" disabled={!question.trim() || !selectedDepartmentId || formState === 'submitting'}>{formState === 'submitting' ? '正在自动派单…' : '提交并自动派单'}</button>
    </form>
    {message ? <p className="error-message">{message}</p> : null}
    {created ? <section className="consultation-success"><strong>咨询已自动派至 {created.selected_department.department_name}</strong><p>您可在下方“我的咨询”查看办理状态和部门答复。</p></section> : null}
    </section>
    <ConsultationList records={records} government={false} />
  </section>
}

function GovernmentConsultations() {
  const { getAccessToken } = useAuth()
  const token = getAccessToken() ?? ''
  const [records, setRecords] = useState<ConsultationRecord[]>([])
  const [message, setMessage] = useState('')
  const [answers, setAnswers] = useState<Record<string, string>>({})
  const [publication, setPublication] = useState<Record<string, boolean>>({})
  const [publicQuestions, setPublicQuestions] = useState<Record<string, string>>({})
  const [publicAnswers, setPublicAnswers] = useState<Record<string, string>>({})
  useEffect(() => { void apiClient.getConsultations(token).then(setRecords).catch((error: unknown) => setMessage(error instanceof ApiError ? error.message : '咨询服务暂不可用。')) }, [token])
  async function reply(record: ConsultationRecord) {
    const answer = answers[record.id]?.trim()
    if (!answer) return
    try {
      const updated = await apiClient.replyToConsultation(record.id, { answer, publishToHistory: !!publication[record.id], publicQuestion: publicQuestions[record.id], publicAnswer: publicAnswers[record.id] }, token)
      setRecords((current) => current.map((item) => item.id === updated.id ? updated : item))
    } catch (error) { setMessage(error instanceof ApiError ? error.message : '答复提交失败。') }
  }
  return <section className="page-content consultation-page"><div className="eyebrow">政府办理</div><h1>咨询办理</h1><p className="lead">这里只显示自动派给当前部门专属账号的工单。答复时可选择是否公开到历史问答。</p>{message ? <p className="error-message">{message}</p> : null}
    <ConsultationList records={records} government answers={answers} setAnswers={setAnswers} publication={publication} setPublication={setPublication} publicQuestions={publicQuestions} setPublicQuestions={setPublicQuestions} publicAnswers={publicAnswers} setPublicAnswers={setPublicAnswers} onReply={reply} />
  </section>
}

export function ConsultationList({ records, government, answers, setAnswers, publication, setPublication, publicQuestions, setPublicQuestions, publicAnswers, setPublicAnswers, onReply }: { records: ConsultationRecord[]; government: boolean; answers?: Record<string, string>; setAnswers?: React.Dispatch<React.SetStateAction<Record<string, string>>>; publication?: Record<string, boolean>; setPublication?: React.Dispatch<React.SetStateAction<Record<string, boolean>>>; publicQuestions?: Record<string, string>; setPublicQuestions?: React.Dispatch<React.SetStateAction<Record<string, string>>>; publicAnswers?: Record<string, string>; setPublicAnswers?: React.Dispatch<React.SetStateAction<Record<string, string>>>; onReply?: (record: ConsultationRecord) => void }) {
  return <section className="consultation-list"><div className="consultation-list-heading"><div><span className="section-label">咨询进度</span><h2>{government ? '待办与已办咨询' : '我的咨询'}</h2></div>{!government ? <p>查看完整提问、当前状态及已办结工单的部门答复。</p> : null}</div>{!records.length ? <p className="muted">暂无咨询工单。</p> : records.map((record) => <ConsultationCard key={record.id} record={record} government={government} answers={answers} setAnswers={setAnswers} publication={publication} setPublication={setPublication} publicQuestions={publicQuestions} setPublicQuestions={setPublicQuestions} publicAnswers={publicAnswers} setPublicAnswers={setPublicAnswers} onReply={onReply} />)}</section>
}

function ConsultationCard({ record, government, answers, setAnswers, publication, setPublication, publicQuestions, setPublicQuestions, publicAnswers, setPublicAnswers, onReply }: { record: ConsultationRecord; government: boolean; answers?: Record<string, string>; setAnswers?: React.Dispatch<React.SetStateAction<Record<string, string>>>; publication?: Record<string, boolean>; setPublication?: React.Dispatch<React.SetStateAction<Record<string, boolean>>>; publicQuestions?: Record<string, string>; setPublicQuestions?: React.Dispatch<React.SetStateAction<Record<string, string>>>; publicAnswers?: Record<string, string>; setPublicAnswers?: React.Dispatch<React.SetStateAction<Record<string, string>>>; onReply?: (record: ConsultationRecord) => void }) {
  const [answerExpanded, setAnswerExpanded] = useState(false)
  const hasLongAnswer = (record.answer_text?.length ?? 0) > 72 || record.answer_text?.includes('\n')
  const status = record.status === 'closed' ? '已办结' : '待办理'

  return <article className="consultation-card"><div className="consultation-card-meta"><span>{record.selected_department.department_name}</span><span className={record.status === 'closed' ? 'consultation-status is-closed' : 'consultation-status'}>{status}</span></div><section className="consultation-question"><strong>我的提问</strong><h3>{record.question_text}</h3></section><p className="consultation-time">提交时间：{new Date(record.created_at).toLocaleString('zh-CN')}</p>{record.answer_text ? <section className="consultation-answer"><div className="consultation-answer-heading"><strong>部门答复</strong>{record.replied_at ? <time dateTime={record.replied_at}>答复时间：{new Date(record.replied_at).toLocaleString('zh-CN')}</time> : null}</div><p className={answerExpanded ? 'is-expanded' : ''}>{record.answer_text}</p>{hasLongAnswer ? <button className="consultation-more" type="button" aria-expanded={answerExpanded} onClick={() => setAnswerExpanded((expanded) => !expanded)}>{answerExpanded ? '收起' : '更多'}</button> : null}</section> : null}{government && record.status === 'assigned' ? <div className="consultation-reply"><label>答复内容<textarea value={answers?.[record.id] ?? ''} onChange={(event) => setAnswers?.((current) => ({ ...current, [record.id]: event.target.value }))} maxLength={8000} /></label><label className="publication-choice"><input type="checkbox" checked={!!publication?.[record.id]} onChange={(event) => setPublication?.((current) => ({ ...current, [record.id]: event.target.checked }))} /> 允许将此答复公开到历史问答</label>{publication?.[record.id] ? <><p className="muted">公开前请人工移除姓名、联系方式、证件号、地址等识别信息；公开版不会自动沿用原始咨询或内部答复。</p><label>去标识化公开问题<textarea value={publicQuestions?.[record.id] ?? ''} onChange={(event) => setPublicQuestions?.((current) => ({ ...current, [record.id]: event.target.value }))} maxLength={4000} /></label><label>去标识化公开答复<textarea value={publicAnswers?.[record.id] ?? ''} onChange={(event) => setPublicAnswers?.((current) => ({ ...current, [record.id]: event.target.value }))} maxLength={8000} /></label></> : null}<button className="button button-primary" type="button" onClick={() => onReply?.(record)}>答复并办结</button></div> : null}</article>
}

function ConsultationState({ title, message }: { title: string; message: string }) { return <section className="page-content policy-state"><div className="eyebrow">部门咨询</div><h1>{title}</h1><p className="lead">{message}</p></section> }

import { useEffect, useRef, useState } from 'react'
import type { ReactNode } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { ApiError, apiClient, type PolicyAnswerResponse } from '../../lib/api/client'
import { useAuth } from '../auth/AuthProvider'

type AnswerState =
  | { status: 'empty' }
  | { status: 'sign_in' }
  | { status: 'loading' }
  | { status: 'success'; result: PolicyAnswerResponse }
  | { status: 'error'; message: string }

type PolicyQaEntryVariant = 'standard' | 'public' | 'workspace'

export function PolicyQaWorkbench({
  compact = false,
  variant = 'standard',
}: {
  compact?: boolean
  variant?: PolicyQaEntryVariant
}) {
  const { state, getAccessToken } = useAuth()
  const [question, setQuestion] = useState('')
  const [answerState, setAnswerState] = useState<AnswerState>({ status: 'empty' })
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const navigate = useNavigate()
  const token = state.status === 'ready' ? getAccessToken() : null
  const eligible = state.status === 'ready' && state.identity.roles.some((role) => role === 'individual' || role === 'enterprise')
  const isEntry = variant !== 'standard'

  useEffect(() => {
    const textarea = textareaRef.current
    if (!textarea) return
    textarea.style.height = 'auto'
    textarea.style.height = `${Math.min(textarea.scrollHeight, 144)}px`
  }, [question])

  async function submit() {
    if (!question.trim()) return
    if (!token) {
      setAnswerState({ status: 'sign_in' })
      return
    }
    if (!eligible) return
    setAnswerState({ status: 'loading' })
    try {
      const result = await apiClient.answerPolicyQuestion(question, token)
      setAnswerState({ status: 'success', result })
    } catch (error) {
      setAnswerState({ status: 'error', message: error instanceof ApiError ? error.message : '政策智能问答暂不可用。' })
    }
  }

  return (
    <section className={`policy-qa-workbench${compact ? ' is-compact' : ''}${isEntry ? ` is-${variant}-entry` : ''}`} aria-label="政策智能问答">
      {isEntry ? <div className="policy-qa-entry-decoration" aria-hidden="true"><span /><span /><span /><span /></div> : null}
      <div className="policy-qa-heading">
        {isEntry ? <>
          <span className="policy-qa-entry-kicker">政通惠 · 深圳政策服务</span>
          <h2><span>你好，</span><strong>有什么可以帮到你？</strong></h2>
          <p>查政策、问办事、了解企业发展支持，都可以从这里开始。</p>
        </> : <>
          <span className="eyebrow">Policy AI Assistant</span>
          <h2>政策智能问答</h2>
          <p>输入个人办事或企业发展问题，获取政策服务指引。</p>
        </>}
      </div>
      {!token || eligible ? <>
        <form className="policy-qa-form" onSubmit={(event) => { event.preventDefault(); void submit() }}>
          <label className="visually-hidden" htmlFor={`policy-question-${variant}`}>你想了解什么政策或服务？</label>
          <textarea ref={textareaRef} id={`policy-question-${variant}`} rows={1} maxLength={4000} value={question} onChange={(event) => setQuestion(event.target.value)} onKeyDown={(event) => {
            if (event.key === 'Enter' && !event.shiftKey) {
              event.preventDefault()
              void submit()
            }
          }} placeholder="说说你遇到的问题…" />
          <div className="policy-qa-actions"><span>{question.trim().length ? `${question.trim().length} / 4000` : '按 Enter 发送，Shift + Enter 换行'}</span><button className="policy-qa-send" type="submit" aria-label={answerState.status === 'loading' ? '正在整理问题' : '提交问题'} disabled={!question.trim() || answerState.status === 'loading'}>{answerState.status === 'loading' ? <span className="policy-qa-send-loader" aria-hidden="true" /> : <svg aria-hidden="true" viewBox="0 0 24 24"><path d="M5 11.5 12 4m0 0 7 7.5M12 4v16" /></svg>}</button></div>
        </form>
        {!token && answerState.status !== 'sign_in' ? <p className="policy-qa-entry-note">登录个人服务或企业服务账号后，即可提交政策问题。</p> : null}
        {answerState.status === 'empty' && variant !== 'workspace' ? <QaState title="从这里开始咨询" message="可咨询政策条件、办理方向或企业发展支持等问题。" /> : null}
        {answerState.status === 'sign_in' ? <QaSignInState /> : null}
        {answerState.status === 'loading' ? <QaState title="正在处理问题" message="正在准备本次政策咨询结果。" pending /> : null}
        {answerState.status === 'error' ? <QaState title="问答暂不可用" message={answerState.message} /> : null}
        {answerState.status === 'success' ? <PolicyAnswerResult result={answerState.result} onConsult={() => navigate(`/consultations?draft=${encodeURIComponent(question.trim())}`)} /> : null}
      </> : <QaState title="当前身份暂不可用" message="个人服务或企业服务身份可使用政策智能问答。" />}
    </section>
  )
}

function QaSignInState() {
  return <QaState title="登录后开始咨询" message="登录个人服务或企业服务账号后，即可提交政策问题。"><Link className="button" to="/login">登录政通惠</Link></QaState>
}

export function PolicyAnswerResult({ result, onConsult }: { result: PolicyAnswerResponse; onConsult?: () => void }) {
  const isPlaceholder = result.answer_mode === 'placeholder'
  return <section className="policy-answer-result" aria-live="polite"><div className="policy-answer-mode"><span>{isPlaceholder ? '演示流程' : '政策检索回答'}</span><small>深圳</small></div><h3>{isPlaceholder ? '咨询结果（演示）' : '咨询结果'}</h3><p className="policy-answer-text">{result.answer}</p>
    {result.notices.map((notice) => <p className="policy-answer-notice" key={notice}>{notice}</p>)}
    {result.sources.length ? <section className="policy-answer-sources"><h4>参考来源</h4>{result.sources.map((source) => <a key={`${source.source_type}-${source.source_id}`} href={source.source_url} target="_blank" rel="noreferrer"><strong>{source.title}</strong>{source.excerpt ? <span>{source.excerpt}</span> : null}</a>)}</section> : <p className="policy-answer-empty-sources">当前演示流程不展示政策来源；真实检索接入后将提供官方来源。</p>}
    <div className="policy-answer-actions"><button className="button button-secondary" type="button" onClick={onConsult}>转为人工咨询</button></div>
  </section>
}

function QaState({ title, message, pending = false, children }: { title: string; message: string; pending?: boolean; children?: ReactNode }) {
  return <section className="policy-qa-state" aria-live="polite" aria-busy={pending}><h3>{title}</h3><p>{message}</p>{children ? <div className="policy-qa-state-action">{children}</div> : null}</section>
}

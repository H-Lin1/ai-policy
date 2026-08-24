import { useState } from 'react'

import { useAuth } from '../auth/AuthProvider'
import { ApiError, apiClient, type ClassificationResponse } from '../../lib/api/client'

type ClassificationState =
  | { status: 'empty' }
  | { status: 'loading' }
  | { status: 'success'; result: ClassificationResponse }
  | { status: 'error'; message: string; notReady: boolean }

export function ClassificationWorkspacePage() {
  const { state, getAccessToken } = useAuth()
  const [text, setText] = useState('')
  const [classificationState, setClassificationState] = useState<ClassificationState>({ status: 'empty' })
  const token = state.status === 'ready' ? getAccessToken() : null

  async function submit() {
    if (!token || !text.trim()) return
    setClassificationState({ status: 'loading' })
    try {
      const result = await apiClient.classify(text, token)
      setClassificationState({ status: 'success', result })
    } catch (error) {
      const apiError = error instanceof ApiError ? error : null
      setClassificationState({
        status: 'error',
        message: apiError?.message ?? '部门分类服务暂不可用。',
        notReady: apiError?.code === 'MODEL_NOT_READY' || apiError?.code === 'MODEL_ASSETS_INVALID',
      })
    }
  }

  if (!token) return <ClassifyState title="需要登录" message="登录后可使用深圳政策部门分类。" />
  return (
    <section className="page-content classify-page">
      <div className="eyebrow">智能分类</div>
      <h1>政策事项部门分类</h1>
      <p className="lead">输入政策事项或咨询内容，系统将推荐最相关的深圳办理部门。</p>
      <form className="classify-form" onSubmit={(event) => { event.preventDefault(); void submit() }}>
        <label htmlFor="classification-text">待分类内容</label>
        <textarea id="classification-text" value={text} onChange={(event) => setText(event.target.value)} placeholder="例如：企业申报科技创新项目资金支持。" maxLength={10000} rows={7} />
        <div className="classify-actions"><span>{text.trim().length ? `${text.trim().length} / 10000` : '请输入内容后开始分类'}</span><button className="button" type="submit" disabled={!text.trim() || classificationState.status === 'loading'}>{classificationState.status === 'loading' ? '正在分类…' : '开始分类'}</button></div>
      </form>
      {classificationState.status === 'empty' ? <ClassifyState title="等待分类" message="分类结果不会保存，提交内容仅用于本次计算。" /> : null}
      {classificationState.status === 'loading' ? <ClassifyState title="正在分析" message="正在使用已验证的深圳部门分类模型。" pending /> : null}
      {classificationState.status === 'error' ? <ClassifyState title={classificationState.notReady ? '模型尚未就绪' : '分类暂不可用'} message={classificationState.message} /> : null}
      {classificationState.status === 'success' ? <ClassificationResultView result={classificationState.result} /> : null}
    </section>
  )
}

export function ClassificationResultView({ result }: { result: ClassificationResponse }) {
  return <section className="classification-results" aria-live="polite"><div className="classification-result-heading"><h2>推荐部门</h2><span>深圳 · {result.model_version}</span></div><div className="classification-list">{result.predictions.map((item, index) => <article className="classification-card" key={item.department_id}><span className="classification-rank">{index + 1}</span><div><h3>{item.department_name}</h3><p>{item.department_id}</p></div><strong>{(item.confidence * 100).toFixed(1)}%</strong></article>)}</div></section>
}

function ClassifyState({ title, message, pending = false }: { title: string; message: string; pending?: boolean }) {
  return <section className="policy-state classify-state" aria-live="polite" aria-busy={pending}><h2>{title}</h2><p>{message}</p></section>
}

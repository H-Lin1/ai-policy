import { useCallback, useEffect, useState } from 'react'

import { ApiError, apiClient, type HealthResponse } from '../../lib/api/client'

type HealthState =
  | { status: 'idle' | 'loading'; data?: undefined; message?: undefined }
  | { status: 'ready'; data: HealthResponse; message?: undefined }
  | { status: 'error'; data?: undefined; message: string }

export function HealthPage() {
  const [state, setState] = useState<HealthState>({ status: 'idle' })

  const loadHealth = useCallback(async () => {
    setState({ status: 'loading' })
    try {
      const data = await apiClient.getHealth()
      setState({ status: 'ready', data })
    } catch (error) {
      const message = error instanceof ApiError ? error.message : '无法连接到后端服务'
      setState({ status: 'error', message })
    }
  }, [])

  useEffect(() => {
    void loadHealth()
  }, [loadHealth])

  const isResponseReady = state.status === 'ready'
  const isDegraded = isResponseReady && state.data.status === 'degraded'
  const isReady = isResponseReady && !isDegraded
  const isLoading = state.status === 'loading'

  return (
    <section className="page-content">
      <div className="eyebrow">工程基础 · 0.1</div>
      <div className="page-heading-row">
        <div>
          <h1>服务状态</h1>
          <p className="lead">检查浏览器与版本化 API 的连接情况。</p>
        </div>
        <button type="button" className="button button-primary" onClick={() => void loadHealth()} disabled={isLoading}>
          {isLoading ? '检查中…' : '重新检查'}
        </button>
      </div>

      <article className={`surface health-card ${isReady ? 'health-ok' : isDegraded ? 'health-degraded' : ''}`} aria-live="polite">
        <div className="health-card-header">
          <div className={`health-icon ${isReady ? 'ok' : isDegraded ? 'degraded' : state.status === 'error' ? 'error' : 'pending'}`} aria-hidden="true">
            {isReady ? '✓' : isDegraded ? '!' : state.status === 'error' ? '!' : '…'}
          </div>
          <div>
            <span className="section-label">API 健康检查</span>
            <h2>
              {isReady ? '服务在线' : isDegraded ? '服务在线，但依赖未就绪' : state.status === 'error' ? '暂时无法连接' : '正在检查'}
            </h2>
          </div>
        </div>
        {isResponseReady && (
          <dl className="health-details">
            <div><dt>服务</dt><dd>{state.data.service ?? 'AI 政策服务'}</dd></div>
            <div><dt>状态</dt><dd>{state.data.status ?? 'unknown'}</dd></div>
            {state.data.version && <div><dt>版本</dt><dd>{state.data.version}</dd></div>}
          </dl>
        )}
        {isDegraded && <p className="muted">请先配置并启动 Supabase/PostgreSQL，再进入业务功能开发。</p>}
        {state.status === 'error' && <p className="error-message">{state.message}</p>}
        {state.status === 'idle' || state.status === 'loading' ? <p className="muted">正在请求配置的 API 地址…</p> : null}
      </article>
    </section>
  )
}

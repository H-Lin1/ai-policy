import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'

import React from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import { StaticRouter } from 'react-router-dom/server.mjs'
import { createServer } from 'vite'

const vite = await createServer({
  appType: 'custom',
  optimizeDeps: { noDiscovery: true },
  server: { middlewareMode: true },
})

try {
  const { PolicyListView, PolicyDetailView, PolicyWorkspacePage } = await vite.ssrLoadModule('/src/app/pages/PolicyWorkspacePage.tsx')
  const { AuthContext } = await vite.ssrLoadModule('/src/app/auth/AuthProvider.tsx')
  const readyAuth = {
    state: { status: 'ready', identity: { subject: 'policy-test', display_name: '测试用户', roles: [], development_bypass: false } },
    hasSession: true,
    signIn: async () => null,
    signOut: async () => undefined,
    retry: () => undefined,
    authorizeRole: async () => { throw new Error('not used') },
    getAccessToken: () => 'test-token',
  }
  const pageShellHtml = renderToStaticMarkup(
    React.createElement(
      StaticRouter,
      { location: '/policies' },
      React.createElement(AuthContext.Provider, { value: readyAuth }, React.createElement(PolicyWorkspacePage)),
    ),
  )
  assert.ok(pageShellHtml.includes('正在读取政策列表'), 'policy page should render its own loading state without FeatureGuard')
  assert.ok(!pageShellHtml.includes('功能尚未开放'), 'policy page must not be blocked by a feature gate')
  const item = {
    id: 'f7425d1e-4777-59dd-86c4-b269d84384b5',
    title: '深圳市医疗保障办法',
    document_no: '市政府令第358号',
    issuing_organization: '深圳市人民政府办公厅',
    source_url: 'https://www.sz.gov.cn/policy/1',
    published_date: '2023-09-09',
    effective_status: 'valid',
  }
  const page = {
    items: [item],
    meta: { page: 1, page_size: 10, total: 20, total_pages: 2, has_next: true, has_previous: false },
  }
  const listHtml = renderToStaticMarkup(
    React.createElement(StaticRouter, { location: '/policies' }, React.createElement(PolicyListView, { page, onPageChange: () => undefined })),
  )
  for (const text of ['政策库', item.title, item.issuing_organization, '查看官方来源', '第 1 / 2 页']) {
    assert.ok(listHtml.includes(text), `policy list should render ${text}`)
  }
  assert.ok(listHtml.includes('disabled=""'), 'previous button should be disabled on first page')

  const detailHtml = renderToStaticMarkup(
    React.createElement(
      StaticRouter,
      { location: '/policies/f7425d1e-4777-59dd-86c4-b269d84384b5' },
      React.createElement(PolicyDetailView, {
        policy: {
          ...item,
          document_url: null,
          collected_at: '2026-08-10T08:43:25Z',
          content_text: '第一条 政策正文\n第二条 继续执行',
          content_sha256: 'a'.repeat(64),
          reference_count: 20,
          source_years: '2025-2026',
        },
      }),
    ),
  )
  for (const text of ['政策详情', '返回政策库', '第一条 政策正文', '第二条 继续执行', '查看官方原文']) {
    assert.ok(detailHtml.includes(text), `policy detail should render ${text}`)
  }

  const styles = await readFile(new URL('../src/styles.css', import.meta.url), 'utf8')
  for (const selector of ['.policy-list', '.policy-card', '.policy-facts', '.policy-content-text']) {
    assert.ok(styles.includes(selector), `policy styles should include ${selector}`)
  }
  assert.ok(styles.includes('.policy-facts { grid-template-columns: 1fr; }'), 'mobile detail facts must use one column')
  process.stdout.write('PASS policy list/detail rendering and responsive styles\n')
} finally {
  await vite.close()
}

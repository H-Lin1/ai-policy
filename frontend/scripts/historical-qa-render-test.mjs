import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'

import React from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import { StaticRouter } from 'react-router-dom/server.mjs'
import { createServer } from 'vite'

const vite = await createServer({ appType: 'custom', optimizeDeps: { noDiscovery: true }, server: { middlewareMode: true } })
try {
  const { HistoricalQaListView, HistoricalQaDetailView } = await vite.ssrLoadModule('/src/app/pages/HistoricalQaWorkspacePage.tsx')
  const item = { id: '374aa395-e753-5f5d-9b9d-25c69f7f83ee', topic: '公积金贷款额度', source_url: 'https://www.sz.gov.cn/hdjlpt/detail?pid=1', replied_at: '2026-08-02T02:00:00Z', publishing_organization: '深圳市人民政府办公厅', contains_legal_basis: true }
  const page = { items: [item], meta: { page: 1, page_size: 10, total: 20, total_pages: 2, has_next: true, has_previous: false } }
  const list = renderToStaticMarkup(React.createElement(StaticRouter, { location: '/qa' }, React.createElement(HistoricalQaListView, { page, onPageChange: () => undefined })))
  for (const text of ['历史问答', item.topic, item.publishing_organization, '查看官方来源', '第 1 / 2 页']) assert.ok(list.includes(text), `list should render ${text}`)
  const detail = renderToStaticMarkup(React.createElement(StaticRouter, { location: '/qa/374aa395-e753-5f5d-9b9d-25c69f7f83ee' }, React.createElement(HistoricalQaDetailView, { record: { ...item, question_text: '请问怎么办理？', answer_text: '您好，请按办事指南提交申请。', question_at: '2026-08-01T01:00:00Z', collected_at: '2026-08-03T03:00:00Z', legal_basis_name: '《办事指南》', legal_basis_citation: '《办事指南》第一条', adjudication_result: '规则对', content_sha256: 'a'.repeat(64) } })))
  for (const text of ['政务问答详情', '返回历史问答', '群众留言', '政府答复', '请问怎么办理？', '《办事指南》第一条']) assert.ok(detail.includes(text), `detail should render ${text}`)
  const styles = await readFile(new URL('../src/styles.css', import.meta.url), 'utf8')
  for (const selector of ['.qa-list', '.qa-card', '.qa-text-section']) assert.ok(styles.includes(selector), `styles should include ${selector}`)
  process.stdout.write('PASS historical Q&A list/detail rendering and responsive styles\n')
} finally { await vite.close() }

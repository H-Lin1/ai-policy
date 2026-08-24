import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'

import React from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import { StaticRouter } from 'react-router-dom/server.mjs'
import { createServer } from 'vite'

const vite = await createServer({ appType: 'custom', optimizeDeps: { noDiscovery: true }, server: { middlewareMode: true } })
try {
  const page = await readFile(new URL('../src/app/pages/ConsultationWorkspacePage.tsx', import.meta.url), 'utf8')
  const client = await readFile(new URL('../src/lib/api/client.ts', import.meta.url), 'utf8')
  const layout = await readFile(new URL('../src/app/AppLayout.tsx', import.meta.url), 'utf8')
  const router = await readFile(new URL('../src/app/router.tsx', import.meta.url), 'utf8')
  const styles = await readFile(new URL('../src/styles.css', import.meta.url), 'utf8')
  const qa = await readFile(new URL('../src/app/pages/PolicyQaWorkbench.tsx', import.meta.url), 'utf8')

  function check(condition, name) {
    assert.ok(condition, name)
    process.stdout.write(`PASS ${name}\n`)
  }

  check(router.includes("path: 'consultations'"), 'consultation route is registered')
  check(layout.includes("label: '政民互动'") && layout.includes("label: '咨询办理'") && !layout.includes("label: '提交咨询'") && !layout.includes("label: '我的咨询'"), 'requester navigation is consolidated into 政民互动')
  check(page.includes('获取部门推荐') && page.includes('推荐部门（仅供选择参考）') && page.includes('最终办理部门'), 'recommendation plus deliberate directory selection render')
  check(page.includes('向政府部门提交咨询工单') && page.includes('我的咨询') && page.includes('我的提问') && page.includes('答复时间') && page.includes("'更多'") && page.includes("'收起'"), 'requester workspace renders submission and consultation progress sections')
  check(page.includes("result.predictions.slice(0, 3)") && page.includes('submit(event: React.FormEvent)'), 'recommendations are capped at three and cannot submit automatically')
  check(page.includes('允许将此答复公开到历史问答') && page.includes('去标识化公开问题') && page.includes('去标识化公开答复'), 'government publication requires explicit deidentified fields')
  check(client.includes('getConsultationDepartments') && client.includes('createConsultation') && client.includes('replyToConsultation'), 'consultation client uses the real API')
  check(qa.includes('转为人工咨询') && qa.includes('navigate(`/consultations?draft='), 'policy QA transfer only navigates to editable consultation draft')
  check(styles.includes('.consultation-page') && styles.includes('.recommendation-list') && styles.includes('.consultation-answer > p.is-expanded') && styles.includes('@media (max-width: 640px)'), 'consultation responsive styles and answer expansion are present')
  check(!styles.includes('.consultation-page { margin-right: calc(50% - 50vw)'), 'consultation page has no viewport-offset centering hack')

  const { ConsultationList } = await vite.ssrLoadModule('/src/app/pages/ConsultationWorkspacePage.tsx')
  const record = {
    id: '374aa395-e753-5f5d-9b9d-25c69f7f83ee',
    selected_department: { department_id: 'sz-department-01', department_name: '测试部门' },
    status: 'assigned', question_text: '请说明办理流程。',
    recommendations: [{ department_id: 'sz-department-01', department_name: '测试部门', confidence: 0.91 }],
    created_at: '2026-08-22T01:00:00Z', assigned_at: '2026-08-22T01:00:00Z',
    answer_text: null, publish_to_history: false, historical_qa_id: null,
  }
  const html = renderToStaticMarkup(React.createElement(StaticRouter, { location: '/consultations' }, React.createElement(ConsultationList, {
    records: [record], government: true, answers: {}, setAnswers: () => undefined,
    publication: {}, setPublication: () => undefined, publicQuestions: {}, setPublicQuestions: () => undefined,
    publicAnswers: {}, setPublicAnswers: () => undefined, onReply: () => undefined,
  })))
  for (const text of ['待办与已办咨询', '测试部门', '请说明办理流程。', '答复内容', '允许将此答复公开到历史问答', '答复并办结']) {
    check(html.includes(text), `government consultation view renders ${text}`)
  }

  const closedRecord = {
    ...record,
    id: '4f84e5d2-6c62-4f6e-9686-5f4efb357918',
    status: 'closed',
    question_text: '请完整说明本事项的办理条件、材料清单和线上提交路径。',
    answer_text: '您可先在线提交申请材料。材料审核通过后，部门将在规定时限内联系您补充所需信息并反馈办理结果。若有特殊情况，请通过官方渠道查询最新办理要求。为便于后续办理，请妥善保留提交凭证，并以部门工作人员的正式通知为准。',
    replied_at: '2026-08-22T02:30:00Z',
    publish_to_history: true,
    historical_qa_id: 'f8bd5f30-525e-4bb6-a552-5b7353d06bf9',
  }
  const requesterHtml = renderToStaticMarkup(React.createElement(StaticRouter, { location: '/consultations' }, React.createElement(ConsultationList, {
    records: [closedRecord], government: false,
  })))
  for (const text of ['我的咨询', '我的提问', closedRecord.question_text, '已办结', '部门答复', '答复时间', '更多']) {
    check(requesterHtml.includes(text), `requester consultation view renders ${text}`)
  }
  check(!requesterHtml.includes('查看已公开历史问答') && !requesterHtml.includes('该答复未公开') && !requesterHtml.includes('允许将此答复公开到历史问答'), 'requester consultation card does not disclose publication state')
} finally {
  await vite.close()
}

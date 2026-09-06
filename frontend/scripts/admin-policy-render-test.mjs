import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'

const router = await readFile(new URL('../src/app/router.tsx', import.meta.url), 'utf8')
const layout = await readFile(new URL('../src/app/AppLayout.tsx', import.meta.url), 'utf8')
const list = await readFile(new URL('../src/app/pages/AdminPoliciesPage.tsx', import.meta.url), 'utf8')
const editor = await readFile(new URL('../src/app/pages/AdminPolicyEditorPage.tsx', import.meta.url), 'utf8')
const client = await readFile(new URL('../src/lib/api/client.ts', import.meta.url), 'utf8')
const styles = await readFile(new URL('../src/styles.css', import.meta.url), 'utf8')

for (const value of ["path: 'policy-management'", "path: 'policy-management/new'"]) assert.ok(router.includes(value), value)
assert.ok(!layout.includes("to: '/policy-management', label: '政策管理'"), 'policy management must not be primary navigation')
for (const value of ['手工录入', '批量 Markdown', 'multiple', '一次最多 20 个 Markdown', '不限制整批总大小', '下载 Markdown 示例', '批量保存草稿', '批量确认发布', '预览']) assert.ok(editor.includes(value), `editor missing ${value}`)
for (const value of ['政策管理', '新增或导入政策', '草稿', '已发布', '已撤回']) assert.ok(list.includes(value), `list missing ${value}`)
for (const value of ['/admin/policies/markdown-parse', '/admin/policies/markdown-example', '/admin/policies']) assert.ok(client.includes(value), `client missing ${value}`)
assert.ok(styles.includes('.policy-fields {') && styles.includes('@media (max-width: 720px)'), 'responsive policy styles missing')
process.stdout.write('PASS admin manual and batch Markdown policy publishing contracts\n')

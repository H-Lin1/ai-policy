import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'

const router = await readFile(new URL('../src/app/router.tsx', import.meta.url), 'utf8')
const layout = await readFile(new URL('../src/app/AppLayout.tsx', import.meta.url), 'utf8')
const home = await readFile(new URL('../src/app/pages/WorkspaceHomePage.tsx', import.meta.url), 'utf8')
const list = await readFile(new URL('../src/app/pages/AdminAccountsPage.tsx', import.meta.url), 'utf8')
const editor = await readFile(new URL('../src/app/pages/AdminAccountEditorPage.tsx', import.meta.url), 'utf8')
const client = await readFile(new URL('../src/lib/api/client.ts', import.meta.url), 'utf8')

assert.ok(!router.includes("path: roleWorkspacePath('admin')"), '/admin role route must be removed')
for (const value of ["path: 'account-management'", "path: 'account-management/new'", "path: 'account-management/:userId'"]) assert.ok(router.includes(value), value)
assert.ok(layout.includes("availableRoles.includes('admin')") && layout.includes('authenticatedUserNavigation.slice(0, 3)'), 'admin navigation must be three items')
for (const text of ['管理员工作台', '账号管理', '注册申请审批', '政策管理', 'to="/account-management"', 'to="/registration-applications"', 'to="/policy-management"']) assert.ok(home.includes(text), `admin homepage missing ${text}`)
for (const text of ['账号管理', '全部角色', '全部状态', '新增账号', '停用', '恢复']) assert.ok(list.includes(text), `account list missing ${text}`)
for (const text of ['新增账号', '编辑账号', '个人', '企业', '政府', '管理员', '保存账号']) assert.ok(editor.includes(text), `account editor missing ${text}`)
for (const path of ['/admin/accounts/counts', '/admin/accounts?', '/admin/accounts/']) assert.ok(client.includes(path), `client missing ${path}`)
process.stdout.write('PASS admin homepage consolidation and account management contracts\n')

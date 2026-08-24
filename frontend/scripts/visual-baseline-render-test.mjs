import assert from 'node:assert/strict'
import { access, readFile } from 'node:fs/promises'

import React from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import { StaticRouter } from 'react-router-dom/server.js'
import { createServer } from 'vite'

const individualImage = new URL('../src/assets/ui1/individual-service.jpg', import.meta.url)
const enterpriseImage = new URL('../src/assets/ui1/enterprise-service.jpg', import.meta.url)

function authValue(state, hasSession = state.status === 'ready') {
  return {
    state,
    hasSession,
    signIn: async () => null,
    signOut: async () => undefined,
    retry: () => undefined,
    getAccessToken: () => 'visual-contract-token',
    authorizeRole: async (role) => ({
      role,
      title: `${role} workspace`,
      subject: 'visual-contract-user',
      region: null,
      organization: null,
    }),
  }
}

function renderWithAuth(Component, auth, initialEntry = '/') {
  return renderToStaticMarkup(
    React.createElement(
      StaticRouter,
      { location: initialEntry },
      React.createElement(
        AuthContext.Provider,
        { value: auth },
        React.createElement(Component),
      ),
    ),
  )
}

function assertIncludes(html, values, context) {
  for (const value of values) {
    assert.ok(html.includes(value), `${context} should render ${value}`)
  }
}

function assertExcludes(html, values, context) {
  for (const value of values) {
    assert.ok(!html.includes(value), `${context} must not render ${value}`)
  }
}

const vite = await createServer({
  appType: 'custom',
  optimizeDeps: { noDiscovery: true },
  server: { middlewareMode: true },
})

let AuthContext

try {
  const { AppLayout } = await vite.ssrLoadModule('/src/app/AppLayout.tsx')
  const { WorkspaceHomePage } = await vite.ssrLoadModule('/src/app/pages/WorkspaceHomePage.tsx')
  const { LoginPage, resolvePostLoginDecision } = await vite.ssrLoadModule('/src/app/pages/LoginPage.tsx')
  const authModule = await vite.ssrLoadModule('/src/app/auth/AuthProvider.tsx')
  AuthContext = authModule.AuthContext

  const signedOut = authValue({ status: 'signed_out' }, false)
  const signedOutLayout = renderWithAuth(AppLayout, signedOut)
  assertExcludes(
    signedOutLayout,
    ['class="site-header"', 'aria-label="主导航"', 'class="account-panel', 'class="sign-out-button"'],
    'signed-out app shell',
  )
  process.stdout.write('PASS visual baseline signed-out home omits global header\n')

  const ready = authValue({
    status: 'ready',
    identity: {
      subject: 'visual-contract-user',
      email: 'visual-contract@example.invalid',
      display_name: '视觉验收用户',
      roles: ['individual', 'admin'],
      role_summaries: [
        { code: 'individual', name: '个人用户' },
        { code: 'admin', name: '平台管理员' },
      ],
      region: { code: 'sz', name: '深圳' },
      organization: null,
      development_bypass: false,
    },
  })
  const readyLayout = renderWithAuth(AppLayout, ready, '/homepage')
  assertIncludes(
    readyLayout,
    [
      '政通惠',
      '首页',
      '政策中心',
      '历史问答',
      '政民互动',
      'class="account-panel is-ready"',
      '视觉验收用户',
      'class="sign-out-button"',
      '退出登录',
      'href="/homepage"',
    ],
    'ready app shell',
  )
  assertExcludes(
    readyLayout,
    ['企业服务', '个人服务', '政府办理', '智能分类', '服务状态', '平台管理', 'href="/admin"', 'class="account-login-link"'],
    'ready app shell',
  )
  process.stdout.write('PASS visual baseline ready app shell role filtering\n')

  const enterpriseReady = authValue({
    status: 'ready',
    identity: {
      subject: 'enterprise-contract-user',
      email: 'enterprise-contract@example.invalid',
      display_name: '企业验收用户',
      roles: ['enterprise'],
      role_summaries: [{ code: 'enterprise', name: '企业用户' }],
      region: { code: 'sz', name: '深圳' },
      organization: { code: 'demo', name: '示例企业', organization_type: 'enterprise' },
      development_bypass: false,
    },
  })
  const enterpriseLayout = renderWithAuth(AppLayout, enterpriseReady)
  assertIncludes(enterpriseLayout, ['首页', '政策中心', '历史问答', '政民互动', '我的企业', 'href="/my-enterprise"'], 'enterprise focused app shell')
  assertExcludes(enterpriseLayout, ['智能分类', '服务状态', '企业服务'], 'enterprise focused app shell')
  process.stdout.write('PASS visual baseline enterprise focused navigation\n')

  const { EnterpriseProfileContent } = await vite.ssrLoadModule('/src/app/pages/EnterpriseProfilePage.tsx')
  const enterpriseProfile = renderWithAuth(EnterpriseProfileContent, enterpriseReady)
  assertIncludes(enterpriseProfile, ['我的企业', '企业基本信息', '示例企业', 'demo', 'enterprise', '深圳', '企业验收用户', 'enterprise-contract@example.invalid', '只读信息'], 'enterprise profile')
  assertExcludes(enterpriseProfile, ['<input', '<textarea', '编辑', '保存'], 'enterprise profile')
  process.stdout.write('PASS enterprise profile renders authorized read-only identity fields\n')

  const authenticatedHome = renderWithAuth(WorkspaceHomePage, enterpriseReady, '/homepage')
  assertIncludes(authenticatedHome, ['class="workspace-home qa-home"', 'policy-qa-workbench'], 'authenticated homepage route')
  assertExcludes(authenticatedHome, ['个人服务', '企业服务', '政府服务'], 'authenticated homepage route')
  const appLayoutSource = await readFile(new URL('../src/app/AppLayout.tsx', import.meta.url), 'utf8')
  assert.ok(appLayoutSource.includes("navigate('/', { replace: true })"), 'sign-out must replace the route with public root')
  process.stdout.write('PASS authenticated homepage route and sign-out redirect contract\n')

  await Promise.all([access(individualImage), access(enterpriseImage)])
  const signedOutHome = renderWithAuth(WorkspaceHomePage, signedOut)
  assertIncludes(
    signedOutHome,
    [
      'class="page-content landing-page"',
      'class="landing-title">政通惠',
      'class="landing-subtitle">一站式政策服务平台',
      'class="service-entry service-entry-individual"',
      'href="/login"',
      'individual-service.jpg',
      'enterprise-service.jpg',
      'alt="个人服务"',
      'alt="企业服务"',
      'alt="政府服务"',
      '个人服务',
      '企业服务',
      '政府服务',
    ],
    'signed-out landing page',
  )
  assert.equal(
    (signedOutHome.match(/class="service-entry service-entry-/g) ?? []).length,
    3,
    'signed-out landing page should render exactly three primary service entries',
  )
  assert.equal(
    (signedOutHome.match(/href="\/login"/g) ?? []).length,
    3,
    'each signed-out service entry should link directly to login',
  )
  assertExcludes(signedOutHome, ['登录政通惠', 'href="/personal"', 'href="/enterprise"', 'href="/government"'], 'signed-out landing page')
  assert.deepEqual(resolvePostLoginDecision('government', ['government']), { kind: 'matched', destination: '/government' })
  assert.deepEqual(resolvePostLoginDecision('individual', ['individual']), { kind: 'matched', destination: '/homepage' })
  assert.deepEqual(resolvePostLoginDecision('enterprise', ['enterprise']), { kind: 'matched', destination: '/homepage' })
  assert.deepEqual(resolvePostLoginDecision('government', ['individual']), { kind: 'mismatch', actualRole: 'individual', destination: '/homepage' })
  assert.deepEqual(resolvePostLoginDecision(null, ['government']), { kind: 'default', destination: '/homepage' })
  const mismatchLogin = renderWithAuth(LoginPage, ready, { pathname: '/login', state: { intendedRole: 'government' } })
  assertIncludes(mismatchLogin, ['role="dialog"', 'aria-modal="true"', '账号类型不匹配', '政府服务', '个人服务', '进入个人服务', '切换政府服务账号'], 'login role mismatch dialog')
  assertExcludes(mismatchLogin, ['visual-contract@example.invalid', 'visual-contract-user', '请输入邮箱', '请输入密码'], 'login role mismatch dialog')
  process.stdout.write('PASS visual baseline login mismatch requires explicit user choice\n')
  process.stdout.write('PASS visual baseline signed-out landing routes and local images\n')
} finally {
  await vite.close()
}

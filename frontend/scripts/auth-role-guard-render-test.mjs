import assert from 'node:assert/strict'

import React from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import { createServer } from 'vite'

const protectedContent = '角色受保护内容'
const identity = {
  subject: '00000000-0000-4000-8000-000000000111',
  email: 'demo@example.com',
  display_name: '演示用户',
  roles: ['individual'],
  role_summaries: [{ code: 'individual', name: '个人' }],
  region: { code: 'sz', name: '深圳市' },
  organization: null,
  development_bypass: false,
}
const workspace = {
  role: 'individual',
  title: '个人服务工作区',
  subject: identity.subject,
  region: identity.region,
  organization: null,
}

const roles = ['individual', 'enterprise', 'government', 'admin']

function roleWorkspace(role, subject = identity.subject) {
  return {
    role,
    title: `${role} workspace`,
    subject,
    region: identity.region,
    organization: null,
  }
}

async function waitFor(predicate, message) {
  for (let attempt = 0; attempt < 50; attempt += 1) {
    if (predicate()) return
    await new Promise((resolve) => setTimeout(resolve, 0))
  }
  assert.fail(message)
}

function deferred() {
  let resolve
  let reject
  const promise = new Promise((promiseResolve, promiseReject) => {
    resolve = promiseResolve
    reject = promiseReject
  })
  return { promise, resolve, reject }
}

const cases = [
  {
    name: 'configuration-missing',
    authState: { status: 'configuration_missing', message: '当前环境尚未配置登录服务' },
    authorization: { status: 'checking' },
    visible: ['登录服务未配置'],
  },
  {
    name: 'identity-loading',
    authState: { status: 'loading' },
    authorization: { status: 'checking' },
    visible: ['正在读取身份'],
  },
  {
    name: 'signed-out',
    authState: { status: 'signed_out' },
    authorization: { status: 'checking' },
    visible: ['需要登录', '登录'],
  },
  {
    name: 'identity-error',
    authState: { status: 'error', message: '身份服务不可用' },
    authorization: { status: 'checking' },
    visible: ['身份暂不可用', '身份服务不可用', '重试'],
  },
  {
    name: 'authorization-checking',
    authState: { status: 'ready', identity },
    authorization: { status: 'checking' },
    visible: ['正在确认权限'],
  },
  {
    name: 'denied',
    authState: { status: 'ready', identity },
    authorization: { status: 'denied' },
    visible: ['无权访问'],
  },
  {
    name: 'authorization-error',
    authState: { status: 'ready', identity },
    authorization: { status: 'error', message: '权限检查失败' },
    visible: ['权限服务暂不可用', '权限检查失败', '重试'],
  },
  {
    name: 'allowed',
    authState: { status: 'ready', identity },
    authorization: { status: 'allowed', workspace },
    visible: [protectedContent],
  },
]

const vite = await createServer({
  appType: 'custom',
  optimizeDeps: { noDiscovery: true },
  server: { middlewareMode: true },
})

try {
  const { RoleGuardView } = await vite.ssrLoadModule('/src/app/auth/RoleGuard.tsx')
  const { RoleAuthorizationCoordinator } = await vite.ssrLoadModule(
    '/src/app/auth/RoleAuthorizationCoordinator.ts',
  )
  const { ApiError } = await vite.ssrLoadModule('/src/lib/api/client.ts')
  const { roleWorkspacePaths } = await vite.ssrLoadModule('/src/app/roleRoutes.ts')

  for (const testCase of cases) {
    const html = renderToStaticMarkup(
      React.createElement(
        RoleGuardView,
        {
          authState: testCase.authState,
          authorization: testCase.authorization,
          retryIdentity: () => undefined,
          retryAuthorization: () => undefined,
        },
        () => React.createElement('div', null, protectedContent),
      ),
    )
    for (const text of testCase.visible) {
      assert.ok(html.includes(text), `${testCase.name} should render ${text}`)
    }
    if (testCase.name !== 'allowed') {
      assert.ok(!html.includes(protectedContent), `${testCase.name} must hide protected content`)
    }
    process.stdout.write(`PASS RoleGuard ${testCase.name}\n`)
  }

  assert.deepEqual(roleWorkspacePaths, {
    individual: '/personal',
    enterprise: '/enterprise',
    government: '/government',
    admin: '/admin',
  })
  process.stdout.write('PASS RoleGuard public role routes\n')

  for (const role of roles) {
    const calls = []
    const coordinator = new RoleAuthorizationCoordinator(async (requestedRole) => {
      calls.push(requestedRole)
      return roleWorkspace(requestedRole)
    })
    const key = `${role}:${identity.subject}`
    coordinator.check(key, role)
    await waitFor(
      () => coordinator.getSnapshot().state.status === 'allowed',
      `${role} should become allowed`,
    )
    assert.deepEqual(calls, [role])
    assert.equal(coordinator.getSnapshot().key, key)
    assert.equal(coordinator.getSnapshot().state.workspace.role, role)
    process.stdout.write(`PASS RoleGuard async allowed ${role}\n`)
  }

  {
    const coordinator = new RoleAuthorizationCoordinator(async () => {
      throw new ApiError('ROLE_FORBIDDEN: 无权访问', 403, { code: 'ROLE_FORBIDDEN' })
    })
    coordinator.check('individual:denied', 'individual')
    await waitFor(
      () => coordinator.getSnapshot().state.status === 'denied',
      '403 should become denied',
    )
    process.stdout.write('PASS RoleGuard async 403 denied\n')
  }

  {
    const coordinator = new RoleAuthorizationCoordinator(async () => {
      throw new ApiError('权限服务不可用', 503, { code: 'AUTHORIZATION_UNAVAILABLE' })
    })
    coordinator.check('enterprise:error', 'enterprise')
    await waitFor(
      () => coordinator.getSnapshot().state.status === 'error',
      'service failure should become error',
    )
    assert.equal(coordinator.getSnapshot().state.message, '权限服务不可用')
    process.stdout.write('PASS RoleGuard async service error\n')
  }

  {
    let attempts = 0
    const coordinator = new RoleAuthorizationCoordinator(async (role) => {
      attempts += 1
      if (attempts === 1) throw new ApiError('权限服务不可用', 503)
      return roleWorkspace(role)
    })
    const key = 'government:retry'
    coordinator.check(key, 'government')
    await waitFor(
      () => coordinator.getSnapshot().state.status === 'error',
      'first authorization attempt should fail',
    )
    coordinator.check(key, 'government')
    assert.equal(coordinator.getSnapshot().state.status, 'checking')
    await waitFor(
      () => coordinator.getSnapshot().state.status === 'allowed',
      'retry should allow access',
    )
    assert.equal(attempts, 2)
    process.stdout.write('PASS RoleGuard async retry\n')
  }

  {
    const stale = deferred()
    const fresh = deferred()
    const coordinator = new RoleAuthorizationCoordinator((role) => {
      return role === 'individual' ? stale.promise : fresh.promise
    })
    const cancelStale = coordinator.check('individual:old-subject', 'individual')
    await new Promise((resolve) => setTimeout(resolve, 0))
    cancelStale()
    coordinator.check('admin:new-subject', 'admin')
    fresh.resolve(roleWorkspace('admin', 'new-subject'))
    await waitFor(
      () => coordinator.getSnapshot().state.status === 'allowed',
      'new authorization should resolve',
    )
    stale.resolve(roleWorkspace('individual', 'old-subject'))
    await new Promise((resolve) => setTimeout(resolve, 0))
    assert.equal(coordinator.getSnapshot().key, 'admin:new-subject')
    assert.equal(coordinator.getSnapshot().state.workspace.role, 'admin')
    process.stdout.write('PASS RoleGuard async stale result is ignored\n')
  }
} finally {
  await vite.close()
}

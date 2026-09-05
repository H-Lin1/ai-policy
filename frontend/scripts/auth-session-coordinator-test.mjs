import assert from 'node:assert/strict'

import { createServer } from 'vite'

const vite = await createServer({
  appType: 'custom',
  optimizeDeps: { noDiscovery: true },
  server: { middlewareMode: true },
})

function session(accessToken) {
  return { access_token: accessToken }
}

function identity(subject, roles = ['individual']) {
  return {
    subject,
    email: `${subject}@example.com`,
    display_name: subject,
    roles,
    role_summaries: roles.map((code) => ({ code, name: code })),
    region: null,
    organization: null,
    development_bypass: false,
  }
}

function workspace(role, subject = 'subject') {
  return { role, title: `${role} workspace`, subject, region: null, organization: null }
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

async function waitFor(predicate, message) {
  for (let attempt = 0; attempt < 50; attempt += 1) {
    if (predicate()) return
    await new Promise((resolve) => setTimeout(resolve, 0))
  }
  assert.fail(message)
}

function fakeGateway({
  getSession = async () => ({ data: { session: null }, error: null }),
  signInWithPassword = async () => ({ data: { session: null }, error: new Error('failed') }),
  signOut = async () => ({ error: null }),
} = {}) {
  let authListener = null
  let unsubscribeCalls = 0
  const gateway = {
    getSession,
    onAuthStateChange(callback) {
      authListener = callback
      return () => {
        unsubscribeCalls += 1
        authListener = null
      }
    },
    signInWithPassword,
    signOut,
  }
  return {
    gateway,
    emit(nextSession) {
      assert.ok(authListener, 'auth listener must be registered before emitting')
      authListener(nextSession)
    },
    unsubscribeCalls: () => unsubscribeCalls,
  }
}

try {
  const { AuthSessionCoordinator } = await vite.ssrLoadModule(
    '/src/app/auth/AuthSessionCoordinator.ts',
  )
  const { ApiError, apiClient } = await vite.ssrLoadModule('/src/lib/api/client.ts')

  {
    const coordinator = new AuthSessionCoordinator({
      auth: null,
      getMe: async () => identity('unused'),
      getWorkspace: async (role) => workspace(role),
    })
    assert.equal(coordinator.getSnapshot().state.status, 'configuration_missing')
    assert.equal(await coordinator.signIn('demo@example.com', 'secret'), '当前环境尚未配置登录服务')
    process.stdout.write('PASS AuthProvider configuration missing\n')
  }

  {
    const restoredSession = session('restore-token')
    const meTokens = []
    const roleCalls = []
    const fake = fakeGateway({
      getSession: async () => ({ data: { session: restoredSession }, error: null }),
    })
    const coordinator = new AuthSessionCoordinator({
      auth: fake.gateway,
      getMe: async (token) => {
        meTokens.push(token)
        return identity('restored-user')
      },
      getWorkspace: async (role, token) => {
        roleCalls.push({ role, token })
        return workspace(role, 'restored-user')
      },
    })
    const stop = coordinator.start()
    await waitFor(
      () => coordinator.getSnapshot().state.status === 'ready',
      'stored session should resolve identity',
    )
    assert.deepEqual(meTokens, ['restore-token'])
    assert.equal(coordinator.getSnapshot().hasSession, true)
    await coordinator.authorizeRole('individual')
    assert.deepEqual(roleCalls, [{ role: 'individual', token: 'restore-token' }])
    stop()
    assert.equal(fake.unsubscribeCalls(), 1)
    process.stdout.write('PASS AuthProvider session restore and session bearer handoff\n')
  }

  {
    const originalFetch = globalThis.fetch
    let request
    globalThis.fetch = async (input, init) => {
      request = { input: String(input), init }
      return {
        ok: true,
        status: 200,
        statusText: 'OK',
        headers: new Headers(),
        json: async () => identity('api-user'),
      }
    }
    try {
      await apiClient.getMe('api-bearer-token')
      assert.equal(request.input, 'http://localhost:8000/api/v1/me')
      assert.equal(new Headers(request.init.headers).get('Authorization'), 'Bearer api-bearer-token')
    } finally {
      globalThis.fetch = originalFetch
    }
    process.stdout.write('PASS AuthProvider /me uses bearer token\n')
  }

  {
    const signedInSession = session('sign-in-token')
    const credentials = []
    let signOutCalls = 0
    let fake
    fake = fakeGateway({
      signInWithPassword: async (value) => {
        credentials.push(value)
        fake.emit(signedInSession)
        return { data: { session: signedInSession }, error: null }
      },
      signOut: async () => {
        signOutCalls += 1
        return { error: null }
      },
    })
    const meTokens = []
    const coordinator = new AuthSessionCoordinator({
      auth: fake.gateway,
      getMe: async (token) => {
        meTokens.push(token)
        return identity('signed-in-user')
      },
      getWorkspace: async (role) => workspace(role),
    })
    const stop = coordinator.start()
    await waitFor(
      () => coordinator.getSnapshot().state.status === 'signed_out',
      'empty stored session should become signed out',
    )
    assert.equal(await coordinator.signIn('demo@example.com', 'secret'), null)
    await waitFor(
      () => coordinator.getSnapshot().state.status === 'ready',
      'sign in should resolve identity',
    )
    assert.deepEqual(credentials, [{ username: 'demo@example.com', password: 'secret' }])
    assert.deepEqual(meTokens, ['sign-in-token'], 'SIGNED_IN event and response must not duplicate /me')

    const signOutPromise = coordinator.signOut()
    assert.equal(coordinator.getSnapshot().state.status, 'signed_out')
    assert.equal(coordinator.getSnapshot().hasSession, false)
    await signOutPromise
    assert.equal(signOutCalls, 1)
    assert.throws(
      () => coordinator.authorizeRole('individual'),
      (error) => error instanceof ApiError && error.status === 401 && error.code === 'AUTH_REQUIRED',
    )
    stop()
    process.stdout.write('PASS AuthProvider sign in and sign out\n')
  }

  {
    const firstSession = session('refresh-token-1')
    const secondSession = session('refresh-token-2')
    const secondIdentity = deferred()
    const meTokens = []
    const fake = fakeGateway({
      getSession: async () => ({ data: { session: firstSession }, error: null }),
    })
    const coordinator = new AuthSessionCoordinator({
      auth: fake.gateway,
      getMe: async (token) => {
        meTokens.push(token)
        if (token === 'refresh-token-2') return secondIdentity.promise
        return identity('identity-before-refresh')
      },
      getWorkspace: async (role) => workspace(role),
    })
    const stop = coordinator.start()
    await waitFor(
      () => coordinator.getSnapshot().state.status === 'ready',
      'first token should resolve',
    )
    fake.emit(secondSession)
    assert.equal(
      coordinator.getSnapshot().state.status,
      'loading',
      'refresh must clear the identity rendered for the prior token',
    )
    secondIdentity.resolve(identity('identity-after-refresh'))
    await waitFor(
      () => coordinator.getSnapshot().state.status === 'ready',
      'refreshed token should resolve',
    )
    assert.equal(coordinator.getSnapshot().state.identity.subject, 'identity-after-refresh')
    assert.deepEqual(meTokens, ['refresh-token-1', 'refresh-token-2'])
    stop()
    process.stdout.write('PASS AuthProvider auth refresh clears and replaces identity\n')
  }

  {
    const currentSession = session('retry-token')
    let getMeCalls = 0
    const fake = fakeGateway({
      getSession: async () => ({ data: { session: currentSession }, error: null }),
    })
    const coordinator = new AuthSessionCoordinator({
      auth: fake.gateway,
      getMe: async () => {
        getMeCalls += 1
        if (getMeCalls === 1) throw new ApiError('身份服务不可用', 503, { code: 'IDENTITY_UNAVAILABLE' })
        return identity('retry-user')
      },
      getWorkspace: async (role) => workspace(role),
    })
    const stop = coordinator.start()
    await waitFor(
      () => coordinator.getSnapshot().state.status === 'error',
      'identity failure should be visible',
    )
    assert.equal(coordinator.getSnapshot().state.code, 'IDENTITY_UNAVAILABLE')
    const retryPromise = coordinator.retry()
    assert.equal(coordinator.getSnapshot().state.status, 'loading')
    await retryPromise
    assert.equal(coordinator.getSnapshot().state.status, 'ready')
    assert.equal(coordinator.getSnapshot().state.identity.subject, 'retry-user')
    assert.equal(getMeCalls, 2)
    stop()
    process.stdout.write('PASS AuthProvider identity retry\n')
  }

  {
    const storedSessionResult = deferred()
    const fake = fakeGateway({ getSession: () => storedSessionResult.promise })
    const coordinator = new AuthSessionCoordinator({
      auth: fake.gateway,
      getMe: async (token) => identity(token),
      getWorkspace: async (role) => workspace(role),
    })
    const stop = coordinator.start()
    fake.emit(session('newer-event-token'))
    await waitFor(
      () => coordinator.getSnapshot().state.status === 'ready',
      'new auth event should resolve while restore is pending',
    )
    storedSessionResult.resolve({ data: { session: session('stale-restored-token') }, error: null })
    await new Promise((resolve) => setTimeout(resolve, 0))
    assert.equal(coordinator.getSnapshot().state.identity.subject, 'newer-event-token')
    stop()
    process.stdout.write('PASS AuthProvider stale restore result is ignored\n')
  }

  {
    const staleIdentity = deferred()
    const fake = fakeGateway({
      getSession: async () => ({ data: { session: session('stale-token') }, error: null }),
    })
    const coordinator = new AuthSessionCoordinator({
      auth: fake.gateway,
      getMe: async (token) => {
        if (token === 'stale-token') return staleIdentity.promise
        return identity('fresh-user')
      },
      getWorkspace: async (role) => workspace(role),
    })
    const stop = coordinator.start()
    await waitFor(
      () => coordinator.getSnapshot().hasSession,
      'stale identity request should begin',
    )
    fake.emit(session('fresh-token'))
    await waitFor(
      () => coordinator.getSnapshot().state.status === 'ready',
      'new token should win',
    )
    staleIdentity.resolve(identity('stale-user'))
    await new Promise((resolve) => setTimeout(resolve, 0))
    assert.equal(coordinator.getSnapshot().state.identity.subject, 'fresh-user')
    stop()
    process.stdout.write('PASS AuthProvider stale identity result is ignored\n')
  }
} finally {
  await vite.close()
}

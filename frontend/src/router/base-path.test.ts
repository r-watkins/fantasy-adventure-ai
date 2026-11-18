import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('@/features/auth/api', () => ({ getMe: vi.fn() }))

const user = { id: '1', email: 'a@example.com', created_at: '2026-01-01T00:00:00Z' }

// The router is a module-level singleton that reads BASE_URL and the browser
// location when it is created, so each case sets those up and then imports a
// fresh copy.
async function loadRouterAt(options: {
  baseUrl: string
  startPath: string
  authenticated: boolean
}) {
  vi.resetModules()
  vi.stubEnv('BASE_URL', options.baseUrl)
  window.history.replaceState({}, '', options.startPath)

  const authApi = await import('@/features/auth/api')
  if (options.authenticated) {
    vi.mocked(authApi.getMe).mockResolvedValue(user)
  } else {
    vi.mocked(authApi.getMe).mockRejectedValue(new Error('Not authenticated'))
  }

  const { router } = await import('./index')
  await router.load()
  return router
}

describe('router basepath', () => {
  beforeEach(() => {
    window.history.replaceState({}, '', '/')
  })

  afterEach(() => {
    vi.unstubAllEnvs()
  })

  it('redirects an unauthenticated visitor to the prefixed welcome route', async () => {
    await loadRouterAt({
      baseUrl: '/fantasy-adventure-ai/',
      startPath: '/fantasy-adventure-ai/saves',
      authenticated: false,
    })

    expect(window.location.pathname).toBe('/fantasy-adventure-ai/')
  })

  it('redirects an authenticated visitor from welcome to the prefixed saves route', async () => {
    await loadRouterAt({
      baseUrl: '/fantasy-adventure-ai/',
      startPath: '/fantasy-adventure-ai/',
      authenticated: true,
    })

    expect(window.location.pathname).toBe('/fantasy-adventure-ai/saves')
  })

  it('builds locations under the prefix', async () => {
    const router = await loadRouterAt({
      baseUrl: '/fantasy-adventure-ai/',
      startPath: '/fantasy-adventure-ai/',
      authenticated: true,
    })

    expect(router.buildLocation({ to: '/new-game' }).href).toBe('/fantasy-adventure-ai/new-game')
  })

  it('keeps root-relative routing at the domain root', async () => {
    await loadRouterAt({ baseUrl: '/', startPath: '/saves', authenticated: false })

    expect(window.location.pathname).toBe('/')
  })
})

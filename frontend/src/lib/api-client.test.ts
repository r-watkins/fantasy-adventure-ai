import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { apiClient, ApiError } from './api-client'

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

describe('apiClient', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn())
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('sends credentials: include on every request', async () => {
    vi.mocked(fetch).mockResolvedValue(jsonResponse(200, { ok: true }))

    await apiClient.get('/api/me')

    expect(fetch).toHaveBeenCalledWith(
      '/api/me',
      expect.objectContaining({ credentials: 'include', method: 'GET' }),
    )
  })

  it('JSON-encodes the request body on post/put/patch', async () => {
    vi.mocked(fetch).mockResolvedValue(jsonResponse(200, { ok: true }))

    await apiClient.post('/api/auth/login', { email: 'a@example.com', password: 'x' })

    const [, init] = vi.mocked(fetch).mock.calls[0]
    expect(init?.method).toBe('POST')
    expect(init?.body).toBe(JSON.stringify({ email: 'a@example.com', password: 'x' }))
  })

  it('returns parsed JSON on success', async () => {
    vi.mocked(fetch).mockResolvedValue(jsonResponse(200, { id: '123', email: 'a@example.com' }))

    const result = await apiClient.get<{ id: string; email: string }>('/api/me')

    expect(result).toEqual({ id: '123', email: 'a@example.com' })
  })

  it('returns undefined for a 204 No Content response', async () => {
    vi.mocked(fetch).mockResolvedValue(new Response(null, { status: 204 }))

    const result = await apiClient.post('/api/auth/logout')

    expect(result).toBeUndefined()
  })

  it('throws ApiError with the parsed detail on a non-2xx response', async () => {
    vi.mocked(fetch).mockResolvedValue(jsonResponse(401, { detail: 'Invalid email or password' }))

    await expect(apiClient.post('/api/auth/login', {})).rejects.toMatchObject({
      status: 401,
      detail: 'Invalid email or password',
    })
  })

  it('ApiError is an instance of Error', async () => {
    vi.mocked(fetch).mockResolvedValue(jsonResponse(409, { detail: 'Email is already registered' }))

    await expect(apiClient.post('/api/auth/register', {})).rejects.toBeInstanceOf(ApiError)
  })
})

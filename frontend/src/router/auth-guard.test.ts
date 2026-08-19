import { afterEach, describe, expect, it, vi } from 'vitest'

import * as authApi from '@/features/auth/api'
import { ApiError } from '@/lib/api-client'

import { fetchCurrentUser } from './auth-guard'

vi.mock('@/features/auth/api')

describe('fetchCurrentUser', () => {
  afterEach(() => {
    vi.resetAllMocks()
  })

  it('returns the user when GET /api/me succeeds', async () => {
    const user = { id: '1', email: 'a@example.com', created_at: '2026-01-01T00:00:00Z' }
    vi.mocked(authApi.getMe).mockResolvedValue(user)

    await expect(fetchCurrentUser()).resolves.toEqual(user)
  })

  it('returns null on a 401 (not authenticated)', async () => {
    vi.mocked(authApi.getMe).mockRejectedValue(new ApiError(401, 'Not authenticated'))

    await expect(fetchCurrentUser()).resolves.toBeNull()
  })

  it('returns null rather than throwing on an unexpected error', async () => {
    vi.mocked(authApi.getMe).mockRejectedValue(new Error('network down'))

    await expect(fetchCurrentUser()).resolves.toBeNull()
  })
})

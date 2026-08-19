import { apiClient } from '@/lib/api-client'

import type { AuthenticatedUser } from './types'

export function registerRequest(email: string, password: string): Promise<AuthenticatedUser> {
  return apiClient.post<AuthenticatedUser>('/api/auth/register', { email, password })
}

export function loginRequest(email: string, password: string): Promise<AuthenticatedUser> {
  return apiClient.post<AuthenticatedUser>('/api/auth/login', { email, password })
}

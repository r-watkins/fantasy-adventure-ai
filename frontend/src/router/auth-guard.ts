import { getMe } from '@/features/auth/api'
import type { AuthenticatedUser } from '@/features/auth/types'

export async function fetchCurrentUser(): Promise<AuthenticatedUser | null> {
  try {
    return await getMe()
  } catch {
    // Not authenticated (401) or a transient error - either way, treat as
    // "no user" for routing purposes rather than crashing navigation.
    return null
  }
}

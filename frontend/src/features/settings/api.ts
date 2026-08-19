import { apiClient } from '@/lib/api-client'
import type { Theme } from '@/components/theme-provider'

export function updateThemeSetting(theme: Theme): Promise<{ theme_preference: Theme }> {
  return apiClient.put<{ theme_preference: Theme }>('/api/me/settings', {
    theme_preference: theme,
  })
}

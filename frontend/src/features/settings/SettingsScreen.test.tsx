import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { ThemeProvider } from '@/components/theme-provider'
import * as authApi from '@/features/auth/api'
import { ApiError } from '@/lib/api-client'

import * as settingsApi from './api'
import { SettingsScreen } from './SettingsScreen'

vi.mock('./api')
vi.mock('@/features/auth/api')

function renderScreen(onLoggedOut = vi.fn()) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <SettingsScreen onLoggedOut={onLoggedOut} />
      </ThemeProvider>
    </QueryClientProvider>,
  )
}

describe('SettingsScreen', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  afterEach(() => {
    vi.resetAllMocks()
  })

  it('marks the current theme as selected', () => {
    renderScreen()

    expect(screen.getByRole('radio', { name: 'System' })).toHaveAttribute('aria-checked', 'true')
    expect(screen.getByRole('radio', { name: 'Dark' })).toHaveAttribute('aria-checked', 'false')
  })

  it('applies the theme locally and persists it via PUT when an option is clicked', async () => {
    vi.mocked(settingsApi.updateThemeSetting).mockResolvedValue({ theme_preference: 'dark' })

    renderScreen()

    fireEvent.click(screen.getByRole('radio', { name: 'Dark' }))

    expect(screen.getByRole('radio', { name: 'Dark' })).toHaveAttribute('aria-checked', 'true')
    await waitFor(() => expect(settingsApi.updateThemeSetting).toHaveBeenCalledWith('dark'))
    expect(localStorage.getItem('fantasy-ai-adventure-theme')).toBe('dark')
  })

  it('shows an error message when persisting the theme fails', async () => {
    vi.mocked(settingsApi.updateThemeSetting).mockRejectedValue(new ApiError(401, 'Not authenticated'))

    renderScreen()
    fireEvent.click(screen.getByRole('radio', { name: 'Light' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('Not authenticated')
  })

  it('logs out and calls onLoggedOut on success', async () => {
    vi.mocked(authApi.logoutRequest).mockResolvedValue(undefined)
    const onLoggedOut = vi.fn()

    renderScreen(onLoggedOut)
    fireEvent.click(screen.getByRole('button', { name: 'Sign out' }))

    await waitFor(() => expect(onLoggedOut).toHaveBeenCalled())
    expect(authApi.logoutRequest).toHaveBeenCalled()
  })
})

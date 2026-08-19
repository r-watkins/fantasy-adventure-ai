import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { ApiError } from '@/lib/api-client'

import * as api from './api'
import { LoginForm } from './LoginForm'

vi.mock('./api')

function renderWithQueryClient(ui: React.ReactElement) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(<QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>)
}

describe('LoginForm', () => {
  afterEach(() => {
    vi.resetAllMocks()
  })

  it('submits the entered email and password', async () => {
    const user = { id: '1', email: 'a@example.com', created_at: '2026-01-01T00:00:00Z' }
    vi.mocked(api.loginRequest).mockResolvedValue(user)
    const onLoggedIn = vi.fn()

    renderWithQueryClient(<LoginForm onLoggedIn={onLoggedIn} />)

    fireEvent.change(screen.getByLabelText('Email'), { target: { value: 'a@example.com' } })
    fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'correct horse' } })
    fireEvent.click(screen.getByRole('button', { name: 'Sign in' }))

    await waitFor(() => expect(onLoggedIn).toHaveBeenCalledWith(user))
    expect(api.loginRequest).toHaveBeenCalledWith('a@example.com', 'correct horse')
  })

  it('shows a generic error message on invalid credentials', async () => {
    vi.mocked(api.loginRequest).mockRejectedValue(new ApiError(401, 'Invalid email or password'))

    renderWithQueryClient(<LoginForm onLoggedIn={vi.fn()} />)

    fireEvent.change(screen.getByLabelText('Email'), { target: { value: 'a@example.com' } })
    fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'wrong' } })
    fireEvent.click(screen.getByRole('button', { name: 'Sign in' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('Invalid email or password')
  })

  it('shows a rate-limit message on 429', async () => {
    vi.mocked(api.loginRequest).mockRejectedValue(new ApiError(429, 'Rate limit exceeded'))

    renderWithQueryClient(<LoginForm onLoggedIn={vi.fn()} />)

    fireEvent.change(screen.getByLabelText('Email'), { target: { value: 'a@example.com' } })
    fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'wrong' } })
    fireEvent.click(screen.getByRole('button', { name: 'Sign in' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('Too many attempts')
  })
})

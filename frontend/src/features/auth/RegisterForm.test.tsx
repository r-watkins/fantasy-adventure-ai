import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { ApiError } from '@/lib/api-client'

import * as api from './api'
import { RegisterForm } from './RegisterForm'

vi.mock('./api')

function renderWithQueryClient(ui: React.ReactElement) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(<QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>)
}

describe('RegisterForm', () => {
  afterEach(() => {
    vi.resetAllMocks()
  })

  it('submits the entered email and password', async () => {
    const user = { id: '1', email: 'a@example.com', created_at: '2026-01-01T00:00:00Z' }
    vi.mocked(api.registerRequest).mockResolvedValue(user)
    const onRegistered = vi.fn()

    renderWithQueryClient(<RegisterForm onRegistered={onRegistered} />)

    fireEvent.change(screen.getByLabelText('Email'), { target: { value: 'a@example.com' } })
    fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'correct horse' } })
    fireEvent.click(screen.getByRole('button', { name: 'Create account' }))

    await waitFor(() => expect(onRegistered).toHaveBeenCalledWith(user))
    expect(api.registerRequest).toHaveBeenCalledWith('a@example.com', 'correct horse')
  })

  it('shows the server error message on duplicate email', async () => {
    vi.mocked(api.registerRequest).mockRejectedValue(
      new ApiError(409, 'Email is already registered'),
    )

    renderWithQueryClient(<RegisterForm onRegistered={vi.fn()} />)

    fireEvent.change(screen.getByLabelText('Email'), { target: { value: 'dup@example.com' } })
    fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'correct horse' } })
    fireEvent.click(screen.getByRole('button', { name: 'Create account' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('Email is already registered')
  })

  it('calls onSwitchToLogin when the footer link is clicked', () => {
    const onSwitchToLogin = vi.fn()
    renderWithQueryClient(<RegisterForm onRegistered={vi.fn()} onSwitchToLogin={onSwitchToLogin} />)

    fireEvent.click(screen.getByText('Already have an account? Sign in'))

    expect(onSwitchToLogin).toHaveBeenCalled()
  })
})

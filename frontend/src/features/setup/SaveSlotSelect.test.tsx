import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { ApiError } from '@/lib/api-client'

import * as savesApi from './saves-api'
import { SaveSlotSelect } from './SaveSlotSelect'
import type { SaveSlotSummary } from './saves-api'

vi.mock('./saves-api')

function renderWithQueryClient(ui: React.ReactElement) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(<QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>)
}

const SAVE: SaveSlotSummary = {
  id: 'save-1',
  name: 'Tavern Cook',
  origin_id: 'tavern_cook',
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-02T00:00:00Z',
  archived_at: null,
}

describe('SaveSlotSelect', () => {
  afterEach(() => {
    vi.resetAllMocks()
  })

  it('renders the list of saves once loaded', async () => {
    vi.mocked(savesApi.listSaves).mockResolvedValue([SAVE])

    renderWithQueryClient(<SaveSlotSelect onContinue={vi.fn()} onNewGame={vi.fn()} />)

    expect(await screen.findByText('Tavern Cook')).toBeInTheDocument()
  })

  it('renders an empty state when there are no saves', async () => {
    vi.mocked(savesApi.listSaves).mockResolvedValue([])

    renderWithQueryClient(<SaveSlotSelect onContinue={vi.fn()} onNewGame={vi.fn()} />)

    expect(await screen.findByText(/no saved adventures yet/i)).toBeInTheDocument()
  })

  it('renders an error message when loading fails', async () => {
    vi.mocked(savesApi.listSaves).mockRejectedValue(new ApiError(500, 'boom'))

    renderWithQueryClient(<SaveSlotSelect onContinue={vi.fn()} onNewGame={vi.fn()} />)

    expect(await screen.findByRole('alert')).toHaveTextContent('boom')
  })

  it('calls onNewGame when New Game is clicked', async () => {
    vi.mocked(savesApi.listSaves).mockResolvedValue([])
    const onNewGame = vi.fn()

    renderWithQueryClient(<SaveSlotSelect onContinue={vi.fn()} onNewGame={onNewGame} />)
    await screen.findByText(/no saved adventures yet/i)

    fireEvent.click(screen.getByRole('button', { name: 'New Game' }))

    expect(onNewGame).toHaveBeenCalled()
  })

  it('calls onContinue with the save id when Continue is clicked', async () => {
    vi.mocked(savesApi.listSaves).mockResolvedValue([SAVE])
    const onContinue = vi.fn()

    renderWithQueryClient(<SaveSlotSelect onContinue={onContinue} onNewGame={vi.fn()} />)
    await screen.findByText('Tavern Cook')

    fireEvent.click(screen.getByRole('button', { name: 'Continue' }))

    expect(onContinue).toHaveBeenCalledWith('save-1')
  })

  it('archives a save only after confirming in the dialog', async () => {
    vi.mocked(savesApi.listSaves).mockResolvedValue([SAVE])
    vi.mocked(savesApi.archiveSave).mockResolvedValue({ ...SAVE, archived_at: '2026-01-03T00:00:00Z' })
    const user = userEvent.setup()

    renderWithQueryClient(<SaveSlotSelect onContinue={vi.fn()} onNewGame={vi.fn()} />)
    await screen.findByText('Tavern Cook')

    // Base UI's popup interactions expect a realistic pointer/click event
    // sequence internally - plain fireEvent.click (a single synthetic
    // 'click') doesn't reliably reach the Action button inside the portal,
    // so this test uses userEvent, which dispatches the full sequence.
    await user.click(screen.getByRole('button', { name: 'Archive' }))
    expect(savesApi.archiveSave).not.toHaveBeenCalled()

    const dialog = await screen.findByRole('alertdialog')
    await user.click(within(dialog).getByRole('button', { name: 'Archive' }))

    // useMutation calls mutationFn as (variables, context), so archiveSave
    // receives a second react-query-internal argument beyond the save id -
    // expected and harmless (archiveSave's own signature ignores it).
    await waitFor(() =>
      expect(savesApi.archiveSave).toHaveBeenCalledWith('save-1', expect.anything()),
    )
  })
})

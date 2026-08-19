import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { ApiError } from '@/lib/api-client'

import * as contentApi from './content-api'
import type { Origin } from './content-api'
import { OriginSelect } from './OriginSelect'
import * as savesApi from './saves-api'
import type { SaveSlotSummary } from './saves-api'

vi.mock('./content-api')
vi.mock('./saves-api')

function renderWithQueryClient(ui: React.ReactElement) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(<QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>)
}

const ORIGINS: Origin[] = [
  {
    id: 'tavern_cook',
    name: 'Tavern Cook',
    tagline: 'Keeper of the hearth',
    description: 'You know the tavern better than anyone.',
    start_location_id: 'ashfen_tavern_kitchen',
    starting_traits: ['resourceful'],
    starting_inventory: [{ item_id: 'iron_cook_knife', quantity: 1 }],
    opening_hook: 'Smoke curls from the kitchen doorway.',
  },
  {
    id: 'wheat_farmer',
    name: 'Wheat Farmer',
    tagline: 'Salt of the earth',
    description: 'The fields are your life, until now.',
    start_location_id: 'ashfen_east_fields',
    starting_traits: ['sturdy'],
    starting_inventory: [{ item_id: 'field_sickle', quantity: 1 }],
    opening_hook: 'The wind carries smoke from the village.',
  },
]

const SAVE: SaveSlotSummary = {
  id: 'save-42',
  name: 'Tavern Cook',
  origin_id: 'tavern_cook',
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
  archived_at: null,
}

describe('OriginSelect', () => {
  afterEach(() => {
    vi.resetAllMocks()
  })

  it('renders both required origins', async () => {
    vi.mocked(contentApi.listOrigins).mockResolvedValue(ORIGINS)

    renderWithQueryClient(<OriginSelect onCreated={vi.fn()} />)

    expect(await screen.findByText('Tavern Cook')).toBeInTheDocument()
    expect(screen.getByText('Wheat Farmer')).toBeInTheDocument()
  })

  it('disables the submit button until an origin is selected', async () => {
    vi.mocked(contentApi.listOrigins).mockResolvedValue(ORIGINS)

    renderWithQueryClient(<OriginSelect onCreated={vi.fn()} />)
    await screen.findByText('Tavern Cook')

    expect(screen.getByRole('button', { name: 'Begin adventure' })).toBeDisabled()

    fireEvent.click(screen.getByRole('radio', { name: /Tavern Cook/ }))

    expect(screen.getByRole('button', { name: 'Begin adventure' })).toBeEnabled()
  })

  it('creates a save with the selected origin and character name, then calls onCreated', async () => {
    vi.mocked(contentApi.listOrigins).mockResolvedValue(ORIGINS)
    vi.mocked(savesApi.createSave).mockResolvedValue(SAVE)
    const onCreated = vi.fn()

    renderWithQueryClient(<OriginSelect onCreated={onCreated} />)
    await screen.findByText('Tavern Cook')

    fireEvent.click(screen.getByRole('radio', { name: /Tavern Cook/ }))
    fireEvent.change(screen.getByLabelText('Character name (optional)'), {
      target: { value: 'Avery' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Begin adventure' }))

    await waitFor(() => expect(onCreated).toHaveBeenCalledWith('save-42'))
    expect(savesApi.createSave).toHaveBeenCalledWith({
      originId: 'tavern_cook',
      characterName: 'Avery',
    })
  })

  it('shows an error message when save creation fails', async () => {
    vi.mocked(contentApi.listOrigins).mockResolvedValue(ORIGINS)
    vi.mocked(savesApi.createSave).mockRejectedValue(new ApiError(422, 'Unknown origin_id'))

    renderWithQueryClient(<OriginSelect onCreated={vi.fn()} />)
    await screen.findByText('Tavern Cook')

    fireEvent.click(screen.getByRole('radio', { name: /Tavern Cook/ }))
    fireEvent.click(screen.getByRole('button', { name: 'Begin adventure' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('Unknown origin_id')
  })
})

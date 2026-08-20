import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import type { Item, Location } from '@/features/setup/content-api'
import * as contentApi from '@/features/setup/content-api'
import type { SaveSlotDetail, SubmitTurnResult } from '@/features/setup/saves-api'
import * as savesApi from '@/features/setup/saves-api'
import { ApiError } from '@/lib/api-client'

import { GameScreen } from './GameScreen'

vi.mock('@/features/setup/content-api')
vi.mock('@/features/setup/saves-api')

const ITEMS: Item[] = [
  {
    id: 'iron_cook_knife',
    name: 'Iron Cook Knife',
    category: 'weapon',
    rarity: 'common',
    description: 'A balanced kitchen knife.',
    tags: [],
    usable_in_prompt: true,
  },
]

const LOCATIONS: Location[] = [
  {
    id: 'ashfen_tavern_kitchen',
    name: 'The Hearth & Thistle Kitchen',
    description: 'A cramped kitchen.',
  },
]

const SAVE: SaveSlotDetail = {
  id: 'save-1',
  name: 'Tavern Cook',
  origin_id: 'tavern_cook',
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
  archived_at: null,
  game_state_json: {
    player: { name: 'Avery', location_id: 'ashfen_tavern_kitchen' },
    inventory: [{ item_id: 'iron_cook_knife', quantity: 1, equipped: true }],
    quests: [{ quest_id: 'missing_ledger', status: 'active', objective: 'Find the ledger.' }],
  },
  messages: [
    {
      role: 'narrator',
      content: 'A cooking fire flares unnaturally blue.',
      turn_number: 0,
      created_at: '2026-01-01T00:00:00Z',
    },
  ],
}

function renderScreen() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <GameScreen saveId="save-1" />
    </QueryClientProvider>
  )
}

describe('GameScreen', () => {
  it('shows an error message when the save fails to load', async () => {
    vi.mocked(contentApi.listItems).mockResolvedValue(ITEMS)
    vi.mocked(contentApi.listLocations).mockResolvedValue(LOCATIONS)
    vi.mocked(savesApi.getSave).mockRejectedValue(new ApiError(404, 'Save not found'))

    renderScreen()

    expect(await screen.findByRole('alert')).toHaveTextContent('Could not load this save.')
  })

  it('renders the save name, transcript, status, and inventory once loaded', async () => {
    vi.mocked(contentApi.listItems).mockResolvedValue(ITEMS)
    vi.mocked(contentApi.listLocations).mockResolvedValue(LOCATIONS)
    vi.mocked(savesApi.getSave).mockResolvedValue(SAVE)

    renderScreen()

    expect(await screen.findByText('Tavern Cook')).toBeInTheDocument()
    expect(screen.getByText('A cooking fire flares unnaturally blue.')).toBeInTheDocument()
    expect(screen.getByText('The Hearth & Thistle Kitchen')).toBeInTheDocument()
    expect(screen.getByText('Find the ledger.')).toBeInTheDocument()
    expect(screen.getByRole('complementary', { name: 'Inventory' })).toBeInTheDocument()
  })

  it('submits a turn and shows the updated transcript after the save is refetched', async () => {
    const user = userEvent.setup()
    vi.mocked(contentApi.listItems).mockResolvedValue(ITEMS)
    vi.mocked(contentApi.listLocations).mockResolvedValue(LOCATIONS)

    const updatedSave: SaveSlotDetail = {
      ...SAVE,
      messages: [
        ...SAVE.messages,
        {
          role: 'player',
          content: 'I inspect the ashes.',
          turn_number: 1,
          created_at: '2026-01-01T00:01:00Z',
        },
        {
          role: 'narrator',
          content: 'Beneath the soot, something glints.',
          turn_number: 1,
          created_at: '2026-01-01T00:01:01Z',
        },
      ],
    }
    vi.mocked(savesApi.getSave).mockResolvedValueOnce(SAVE).mockResolvedValueOnce(updatedSave)

    const turnResult: SubmitTurnResult = {
      player_message: { id: 'p1', role: 'player', content: 'I inspect the ashes.' },
      narrator_message: { id: 'n1', role: 'narrator', content: 'Beneath the soot, something glints.' },
      game_state: SAVE.game_state_json,
      turn_number: 1,
    }
    vi.mocked(savesApi.submitTurn).mockResolvedValue(turnResult)

    renderScreen()
    await screen.findByText('Tavern Cook')

    await user.type(screen.getByLabelText('What do you do?'), 'I inspect the ashes.')
    await user.click(screen.getByRole('button', { name: 'Send' }))

    expect(await screen.findByText('Beneath the soot, something glints.')).toBeInTheDocument()
    expect(savesApi.submitTurn).toHaveBeenCalledWith('save-1', 'I inspect the ashes.')
  })

  it('shows an error near the composer when a turn submission fails', async () => {
    const user = userEvent.setup()
    vi.mocked(contentApi.listItems).mockResolvedValue(ITEMS)
    vi.mocked(contentApi.listLocations).mockResolvedValue(LOCATIONS)
    vi.mocked(savesApi.getSave).mockResolvedValue(SAVE)
    vi.mocked(savesApi.submitTurn).mockRejectedValue(
      new ApiError(502, "The narrator's response could not be processed. Please try again.")
    )

    renderScreen()
    await screen.findByText('Tavern Cook')

    await user.type(screen.getByLabelText('What do you do?'), 'I try something risky.')
    await user.click(screen.getByRole('button', { name: 'Send' }))

    expect(await screen.findByRole('alert')).toHaveTextContent(
      "The narrator's response could not be processed. Please try again."
    )
    expect(screen.getByLabelText('What do you do?')).toHaveValue('I try something risky.')
  })

  it('inserts an inventory item name into the composer when clicked', async () => {
    const user = userEvent.setup()
    vi.mocked(contentApi.listItems).mockResolvedValue(ITEMS)
    vi.mocked(contentApi.listLocations).mockResolvedValue(LOCATIONS)
    vi.mocked(savesApi.getSave).mockResolvedValue(SAVE)

    renderScreen()
    await screen.findByText('Tavern Cook')

    const panel = screen.getByRole('complementary', { name: 'Inventory' })
    await user.click(within(panel).getByText('Iron Cook Knife'))

    await waitFor(() =>
      expect(screen.getByLabelText('What do you do?')).toHaveValue('Iron Cook Knife')
    )
  })
})

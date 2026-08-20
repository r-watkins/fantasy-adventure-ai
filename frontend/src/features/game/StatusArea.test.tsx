import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import type { Location } from '@/features/setup/content-api'
import type { Quest } from '@/features/setup/saves-api'

import { StatusArea } from './StatusArea'

const LOCATIONS: Location[] = [
  {
    id: 'ashfen_tavern_kitchen',
    name: 'The Hearth & Thistle Kitchen',
    description: 'A cramped, warm kitchen.',
  },
]

describe('StatusArea', () => {
  it('shows the resolved location name', () => {
    render(<StatusArea locationId="ashfen_tavern_kitchen" locations={LOCATIONS} quests={[]} />)

    expect(screen.getByText('The Hearth & Thistle Kitchen')).toBeInTheDocument()
  })

  it('falls back to the raw location_id when no matching location is found', () => {
    render(<StatusArea locationId="unknown_location" locations={LOCATIONS} quests={[]} />)

    expect(screen.getByText('unknown_location')).toBeInTheDocument()
  })

  it('shows a placeholder when there are no active quests', () => {
    render(<StatusArea locationId="ashfen_tavern_kitchen" locations={LOCATIONS} quests={[]} />)

    expect(screen.getByText('No active objective')).toBeInTheDocument()
  })

  it('shows only active quest objectives, not completed or failed ones', () => {
    const quests: Quest[] = [
      { quest_id: 'missing_ledger', status: 'active', objective: 'Find the ledger.' },
      { quest_id: 'old_quest', status: 'completed', objective: 'Already done.' },
      { quest_id: 'lost_cause', status: 'failed', objective: 'Never happened.' },
    ]

    render(<StatusArea locationId="ashfen_tavern_kitchen" locations={LOCATIONS} quests={quests} />)

    expect(screen.getByText('Find the ledger.')).toBeInTheDocument()
    expect(screen.queryByText('Already done.')).not.toBeInTheDocument()
    expect(screen.queryByText('Never happened.')).not.toBeInTheDocument()
    expect(screen.queryByText('No active objective')).not.toBeInTheDocument()
  })
})

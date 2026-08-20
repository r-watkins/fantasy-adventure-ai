import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import type { Item } from '@/features/setup/content-api'
import type { InventoryEntry } from '@/features/setup/saves-api'

import { Inventory } from './Inventory'

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

const INVENTORY: InventoryEntry[] = [{ item_id: 'iron_cook_knife', quantity: 1, equipped: true }]

describe('Inventory', () => {
  it('shows item details in the persistent desktop panel', () => {
    render(<Inventory items={ITEMS} inventory={INVENTORY} onSelectItem={vi.fn()} />)

    const panel = screen.getByRole('complementary', { name: 'Inventory' })
    expect(within(panel).getByText('Iron Cook Knife')).toBeInTheDocument()
  })

  it('calls onSelectItem when an item in the desktop panel is clicked', async () => {
    const user = userEvent.setup()
    const onSelectItem = vi.fn()
    render(<Inventory items={ITEMS} inventory={INVENTORY} onSelectItem={onSelectItem} />)

    const panel = screen.getByRole('complementary', { name: 'Inventory' })
    await user.click(within(panel).getByText('Iron Cook Knife'))

    expect(onSelectItem).toHaveBeenCalledWith('Iron Cook Knife')
  })

  it('shows the item count on the mobile drawer trigger', () => {
    render(<Inventory items={ITEMS} inventory={INVENTORY} onSelectItem={vi.fn()} />)

    expect(screen.getByRole('button', { name: 'Inventory (1)' })).toBeInTheDocument()
  })

  it('opens the drawer and shows the same item, calling onSelectItem on click', async () => {
    const user = userEvent.setup()
    const onSelectItem = vi.fn()
    render(<Inventory items={ITEMS} inventory={INVENTORY} onSelectItem={onSelectItem} />)

    await user.click(screen.getByRole('button', { name: 'Inventory (1)' }))

    const dialog = await screen.findByRole('dialog')
    const itemButton = within(dialog).getByText('Iron Cook Knife')
    await user.click(itemButton)

    expect(onSelectItem).toHaveBeenCalledWith('Iron Cook Knife')
  })
})

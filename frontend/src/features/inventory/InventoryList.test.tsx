import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import { InventoryList } from './InventoryList'
import type { InventoryItemView } from './inventoryView'

const ITEMS: InventoryItemView[] = [
  {
    itemId: 'iron_cook_knife',
    name: 'Iron Cook Knife',
    description: 'A balanced kitchen knife.',
    category: 'weapon',
    quantity: 1,
    equipped: true,
  },
  {
    itemId: 'ember_charm',
    name: 'Ember Charm',
    description: 'A warm pendant.',
    category: 'trinket',
    quantity: 3,
    equipped: false,
  },
]

describe('InventoryList', () => {
  it('shows an empty state when there are no items', () => {
    render(<InventoryList items={[]} onSelectItem={vi.fn()} />)

    expect(screen.getByText('Your pack is empty.')).toBeInTheDocument()
  })

  it('renders name, description, category, quantity, and equipped state', () => {
    render(<InventoryList items={ITEMS} onSelectItem={vi.fn()} />)

    expect(screen.getByText('Iron Cook Knife')).toBeInTheDocument()
    expect(screen.getByText('A balanced kitchen knife.')).toBeInTheDocument()
    expect(screen.getByText('weapon')).toBeInTheDocument()
    expect(screen.getByText('Equipped')).toBeInTheDocument()

    expect(screen.getByText('Ember Charm')).toBeInTheDocument()
    expect(screen.getByText('×3')).toBeInTheDocument()
  })

  it('does not show a quantity badge for a single-quantity item', () => {
    render(<InventoryList items={[ITEMS[0]]} onSelectItem={vi.fn()} />)

    expect(screen.queryByText('×1')).not.toBeInTheDocument()
  })

  it('calls onSelectItem with the item name when clicked', () => {
    const onSelectItem = vi.fn()
    render(<InventoryList items={ITEMS} onSelectItem={onSelectItem} />)

    fireEvent.click(screen.getByText('Ember Charm'))

    expect(onSelectItem).toHaveBeenCalledWith('Ember Charm')
  })
})

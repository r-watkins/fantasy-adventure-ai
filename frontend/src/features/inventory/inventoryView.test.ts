import { describe, expect, it } from 'vitest'

import type { Item } from '@/features/setup/content-api'
import type { InventoryEntry } from '@/features/setup/saves-api'

import { buildInventoryView } from './inventoryView'

const KNIFE: Item = {
  id: 'iron_cook_knife',
  name: 'Iron Cook Knife',
  category: 'weapon',
  rarity: 'common',
  description: 'A balanced kitchen knife.',
  tags: ['starting_item'],
  usable_in_prompt: true,
}

const CHARM: Item = {
  id: 'ember_charm',
  name: 'Ember Charm',
  category: 'trinket',
  rarity: 'uncommon',
  description: 'A warm pendant.',
  tags: ['magic'],
  usable_in_prompt: true,
}

describe('buildInventoryView', () => {
  it('joins inventory entries with their content registry details', () => {
    const inventory: InventoryEntry[] = [
      { item_id: 'iron_cook_knife', quantity: 1, equipped: true },
      { item_id: 'ember_charm', quantity: 2, equipped: false },
    ]

    const result = buildInventoryView(inventory, [KNIFE, CHARM])

    expect(result).toEqual([
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
        quantity: 2,
        equipped: false,
      },
    ])
  })

  it('skips inventory entries with no matching content registry item', () => {
    const inventory: InventoryEntry[] = [{ item_id: 'unknown_item', quantity: 1, equipped: false }]

    const result = buildInventoryView(inventory, [KNIFE])

    expect(result).toEqual([])
  })

  it('returns an empty list for an empty inventory', () => {
    expect(buildInventoryView([], [KNIFE, CHARM])).toEqual([])
  })
})

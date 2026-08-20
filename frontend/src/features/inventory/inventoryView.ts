import type { Item } from '@/features/setup/content-api'
import type { InventoryEntry } from '@/features/setup/saves-api'

export interface InventoryItemView {
  itemId: string
  name: string
  description: string
  category: string
  quantity: number
  equipped: boolean
}

// game_state.inventory only carries item_id/quantity/equipped - display
// fields (name/description/category) come from the content registry, so
// this joins the two per source doc §7's inventory rules.
export function buildInventoryView(
  inventory: InventoryEntry[],
  items: Item[]
): InventoryItemView[] {
  const itemsById = new Map(items.map((item) => [item.id, item]))

  return inventory.flatMap((entry) => {
    const item = itemsById.get(entry.item_id)
    if (!item) return []

    return [
      {
        itemId: item.id,
        name: item.name,
        description: item.description,
        category: item.category,
        quantity: entry.quantity,
        equipped: entry.equipped,
      },
    ]
  })
}

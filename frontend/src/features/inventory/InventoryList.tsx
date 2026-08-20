import { Badge } from '@/components/ui/badge'

import type { InventoryItemView } from './inventoryView'

interface InventoryListProps {
  items: InventoryItemView[]
  onSelectItem: (name: string) => void
}

export function InventoryList({ items, onSelectItem }: InventoryListProps) {
  if (items.length === 0) {
    return <p className="text-sm text-muted-foreground">Your pack is empty.</p>
  }

  return (
    <ul className="flex flex-col gap-2">
      {items.map((item) => (
        <li key={item.itemId}>
          <button
            type="button"
            onClick={() => onSelectItem(item.name)}
            className="flex min-h-11 w-full flex-col gap-1 rounded-lg border border-border p-3 text-left transition-colors hover:bg-muted"
          >
            <div className="flex items-center justify-between gap-2">
              <span className="font-medium">{item.name}</span>
              {item.quantity > 1 && <Badge variant="secondary">×{item.quantity}</Badge>}
            </div>
            <p className="text-sm text-muted-foreground">{item.description}</p>
            <div className="flex items-center gap-2">
              <Badge variant="outline">{item.category}</Badge>
              {item.equipped && <Badge>Equipped</Badge>}
            </div>
          </button>
        </li>
      ))}
    </ul>
  )
}

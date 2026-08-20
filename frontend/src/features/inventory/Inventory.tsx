import { Button } from '@/components/ui/button'
import { Drawer, DrawerContent, DrawerHeader, DrawerTitle, DrawerTrigger } from '@/components/ui/drawer'
import type { Item } from '@/features/setup/content-api'
import type { InventoryEntry } from '@/features/setup/saves-api'

import { InventoryList } from './InventoryList'
import { buildInventoryView } from './inventoryView'

interface InventoryProps {
  items: Item[]
  inventory: InventoryEntry[]
  onSelectItem: (name: string) => void
}

// Persistent panel on desktop (lg+), bottom-sheet Drawer on small screens -
// per source doc's responsive requirements and design.md's Task 37 pick
// (Drawer over Sheet: purpose-built swipeable bottom sheet, matches "mobile
// bottom-sheet pattern" more directly than Sheet's generic side="bottom").
export function Inventory({ items, inventory, onSelectItem }: InventoryProps) {
  const view = buildInventoryView(inventory, items)

  return (
    <>
      <aside
        aria-label="Inventory"
        className="hidden w-72 shrink-0 flex-col gap-3 border-l border-border p-4 lg:flex"
      >
        <h2 className="text-sm font-semibold">Inventory</h2>
        <InventoryList items={view} onSelectItem={onSelectItem} />
      </aside>

      <div className="lg:hidden">
        <Drawer swipeDirection="down" showSwipeHandle>
          <DrawerTrigger render={<Button variant="outline" className="min-h-11" />}>
            Inventory{view.length > 0 ? ` (${view.length})` : ''}
          </DrawerTrigger>
          <DrawerContent>
            <DrawerHeader>
              <DrawerTitle>Inventory</DrawerTitle>
            </DrawerHeader>
            <div className="overflow-y-auto p-4">
              <InventoryList items={view} onSelectItem={onSelectItem} />
            </div>
          </DrawerContent>
        </Drawer>
      </div>
    </>
  )
}

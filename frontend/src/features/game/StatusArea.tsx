import { Badge } from '@/components/ui/badge'
import type { Location } from '@/features/setup/content-api'
import type { Quest } from '@/features/setup/saves-api'

interface StatusAreaProps {
  locationId: string
  locations: Location[]
  quests: Quest[]
}

export function StatusArea({ locationId, locations, quests }: StatusAreaProps) {
  const location = locations.find((candidate) => candidate.id === locationId)
  const activeQuests = quests.filter((quest) => quest.status === 'active')

  return (
    <div className="flex flex-wrap items-center gap-2 border-b border-border px-4 py-2 text-sm">
      <Badge variant="outline">{location?.name ?? locationId}</Badge>
      {activeQuests.length === 0 ? (
        <span className="text-muted-foreground">No active objective</span>
      ) : (
        <ul className="flex flex-wrap items-center gap-2">
          {activeQuests.map((quest) => (
            <li key={quest.quest_id} className="text-muted-foreground">
              {quest.objective}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useRef } from 'react'

import { describeApiError } from '@/lib/api-client'
import { listItems, listLocations } from '@/features/setup/content-api'
import { getSave, submitTurn } from '@/features/setup/saves-api'
import { Inventory } from '@/features/inventory/Inventory'

import { ChatTranscript } from './ChatTranscript'
import { Composer, type ComposerHandle } from './Composer'
import { StatusArea } from './StatusArea'

interface GameScreenProps {
  saveId: string
}

export function GameScreen({ saveId }: GameScreenProps) {
  const queryClient = useQueryClient()
  const composerRef = useRef<ComposerHandle>(null)

  const saveQuery = useQuery({ queryKey: ['saves', saveId], queryFn: () => getSave(saveId) })
  const itemsQuery = useQuery({ queryKey: ['content', 'items'], queryFn: listItems })
  const locationsQuery = useQuery({ queryKey: ['content', 'locations'], queryFn: listLocations })

  const turnMutation = useMutation({
    mutationFn: (message: string) => submitTurn(saveId, message),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['saves', saveId] }),
  })

  if (saveQuery.isLoading) {
    return <p className="text-sm text-muted-foreground">Loading your adventure…</p>
  }

  if (saveQuery.isError || !saveQuery.data) {
    return (
      <p role="alert" className="text-sm text-destructive">
        Could not load this save.
      </p>
    )
  }

  const { name, game_state_json: state, messages } = saveQuery.data
  const isTurnInFlight = turnMutation.isPending || saveQuery.isFetching

  async function handleSubmit(message: string) {
    await turnMutation.mutateAsync(message)
  }

  function handleSelectItem(itemName: string) {
    composerRef.current?.insertText(itemName)
  }

  return (
    <div className="flex h-full w-full max-w-5xl flex-1 flex-col overflow-hidden lg:flex-row-reverse">
      <Inventory
        items={itemsQuery.data ?? []}
        inventory={state.inventory}
        onSelectItem={handleSelectItem}
      />

      <div className="flex min-h-0 flex-1 flex-col">
        <h1 className="border-b border-border px-4 py-2 text-sm font-medium">{name}</h1>
        <StatusArea
          locationId={state.player.location_id}
          locations={locationsQuery.data ?? []}
          quests={state.quests}
        />
        <div className="min-h-0 flex-1">
          <ChatTranscript messages={messages} pending={isTurnInFlight} />
        </div>
        <div className="border-t border-border p-4">
          <Composer
            ref={composerRef}
            onSubmit={handleSubmit}
            errorMessage={
              turnMutation.isError
                ? describeApiError(
                    turnMutation.error,
                    'Could not reach the narrator. Please try again.'
                  )
                : null
            }
          />
        </div>
      </div>
    </div>
  )
}

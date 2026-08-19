import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { describeApiError } from '@/lib/api-client'

import { archiveSave, listSaves, type SaveSlotSummary } from './saves-api'

const SAVES_QUERY_KEY = ['saves'] as const

interface SaveSlotSelectProps {
  onContinue: (saveId: string) => void
  onNewGame: () => void
}

export function SaveSlotSelect({ onContinue, onNewGame }: SaveSlotSelectProps) {
  const queryClient = useQueryClient()
  const savesQuery = useQuery({ queryKey: SAVES_QUERY_KEY, queryFn: listSaves })

  const archiveMutation = useMutation({
    mutationFn: archiveSave,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: SAVES_QUERY_KEY })
    },
  })

  return (
    <div className="flex w-full max-w-md flex-col gap-4">
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-medium">Your adventures</h1>
        <Button onClick={onNewGame}>New Game</Button>
      </div>

      {savesQuery.isLoading && (
        <div
          className="flex flex-col gap-3"
          aria-busy="true"
          aria-label="Loading saved adventures"
        >
          <Skeleton className="h-20 w-full" />
          <Skeleton className="h-20 w-full" />
        </div>
      )}

      {savesQuery.isError && (
        <p role="alert" className="text-sm text-destructive">
          {describeApiError(savesQuery.error, 'Could not load your saved adventures.')}
        </p>
      )}

      {savesQuery.data?.length === 0 && (
        <p className="text-sm text-muted-foreground">
          No saved adventures yet. Start a new game to begin.
        </p>
      )}

      {savesQuery.data?.map((save) => (
        <SaveSlotCard
          key={save.id}
          save={save}
          onContinue={() => onContinue(save.id)}
          onArchive={() => archiveMutation.mutate(save.id)}
          isArchiving={archiveMutation.isPending && archiveMutation.variables === save.id}
        />
      ))}
    </div>
  )
}

interface SaveSlotCardProps {
  save: SaveSlotSummary
  onContinue: () => void
  onArchive: () => void
  isArchiving: boolean
}

function SaveSlotCard({ save, onContinue, onArchive, isArchiving }: SaveSlotCardProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{save.name}</CardTitle>
        <CardDescription>
          Last played {new Date(save.updated_at).toLocaleDateString()}
        </CardDescription>
      </CardHeader>
      <CardFooter className="justify-between">
        <AlertDialog>
          <AlertDialogTrigger render={<Button variant="outline" disabled={isArchiving} />}>
            {isArchiving ? 'Archiving…' : 'Archive'}
          </AlertDialogTrigger>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Archive &ldquo;{save.name}&rdquo;?</AlertDialogTitle>
              <AlertDialogDescription>
                This save will be hidden from your adventure list. This can&apos;t be undone from
                here.
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel>Cancel</AlertDialogCancel>
              <AlertDialogAction onClick={onArchive}>Archive</AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
        <Button onClick={onContinue}>Continue</Button>
      </CardFooter>
    </Card>
  )
}

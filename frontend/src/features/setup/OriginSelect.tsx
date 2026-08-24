import { useMutation, useQuery } from '@tanstack/react-query'
import { useState, type FormEvent } from 'react'

import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Skeleton } from '@/components/ui/skeleton'
import { describeApiError } from '@/lib/api-client'
import { cn } from '@/lib/utils'

import { listOrigins } from './content-api'
import { createSave } from './saves-api'

interface OriginSelectProps {
  onCreated: (saveId: string) => void
  onBack?: () => void
}

export function OriginSelect({ onCreated, onBack }: OriginSelectProps) {
  const [selectedOriginId, setSelectedOriginId] = useState<string | null>(null)
  const [characterName, setCharacterName] = useState('')

  const originsQuery = useQuery({ queryKey: ['content', 'origins'], queryFn: listOrigins })

  const createMutation = useMutation({
    mutationFn: () =>
      createSave({
        originId: selectedOriginId!,
        characterName: characterName.trim() || undefined,
      }),
    onSuccess: (save) => onCreated(save.id),
  })

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (selectedOriginId) {
      createMutation.mutate()
    }
  }

  const errorMessage = createMutation.isError
    ? describeApiError(createMutation.error, 'Could not start a new game. Please try again.')
    : null

  return (
    <form onSubmit={handleSubmit} className="flex w-full max-w-2xl flex-col gap-6">
      <div>
        <h1 className="text-lg font-medium">Choose your origin</h1>
        <p className="text-sm text-muted-foreground">
          This shapes where you begin and what you start with.
        </p>
      </div>

      {originsQuery.isLoading && (
        <div
          className="grid grid-cols-1 gap-4 sm:grid-cols-2"
          aria-busy="true"
          aria-label="Loading origins"
        >
          <Skeleton className="h-40 w-full" />
          <Skeleton className="h-40 w-full" />
        </div>
      )}

      {originsQuery.isError && (
        <p role="alert" className="text-sm text-destructive">
          {describeApiError(originsQuery.error, 'Could not load origins.')}
        </p>
      )}

      {originsQuery.data && originsQuery.data.length > 0 && (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2" role="radiogroup" aria-label="Origin">
          {originsQuery.data.map((origin) => {
            const isSelected = selectedOriginId === origin.id
            return (
              // WAI-ARIA APG's button-based radiogroup pattern (same reasoning
              // as SettingsScreen.tsx's theme picker) - a native
              // <input type="radio"> can't carry this card-styled layout.
              <button
                key={origin.id}
                type="button"
                // oxlint-disable-next-line jsx-a11y/prefer-tag-over-role
                role="radio"
                aria-checked={isSelected}
                aria-label={origin.name}
                onClick={() => setSelectedOriginId(origin.id)}
                className="text-left"
              >
                <Card
                  className={cn(
                    'h-full transition-colors',
                    isSelected && 'ring-2 ring-primary',
                  )}
                >
                  <CardHeader>
                    <CardTitle>{origin.name}</CardTitle>
                    <CardDescription>{origin.tagline}</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-muted-foreground">{origin.description}</p>
                  </CardContent>
                </Card>
              </button>
            )
          })}
        </div>
      )}

      <div className="flex flex-col gap-2">
        <Label htmlFor="character-name">Character name (optional)</Label>
        <Input
          id="character-name"
          value={characterName}
          onChange={(event) => setCharacterName(event.target.value)}
          placeholder="Traveler"
          maxLength={64}
        />
      </div>

      {errorMessage && (
        <p role="alert" className="text-sm text-destructive">
          {errorMessage}
        </p>
      )}

      <div className="flex items-center justify-between gap-3">
        {onBack && (
          <Button type="button" variant="outline" onClick={onBack}>
            Back
          </Button>
        )}
        <Button
          type="submit"
          disabled={!selectedOriginId || createMutation.isPending}
          className="ml-auto"
        >
          {createMutation.isPending ? 'Starting…' : 'Begin adventure'}
        </Button>
      </div>
    </form>
  )
}

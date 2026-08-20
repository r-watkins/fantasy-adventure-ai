import { useId, useState, type FormEvent, type KeyboardEvent } from 'react'

import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'

interface ComposerProps {
  onSubmit: (message: string) => Promise<void>
  errorMessage?: string | null
}

export function Composer({ onSubmit, errorMessage = null }: ComposerProps) {
  const [value, setValue] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const textareaId = useId()
  const errorId = useId()

  async function submit() {
    const trimmed = value.trim()
    if (!trimmed || isSubmitting) return

    setIsSubmitting(true)
    try {
      await onSubmit(trimmed)
      setValue('')
    } catch {
      // Leave the typed text in place so the player can retry - the parent
      // is responsible for surfacing errorMessage.
    } finally {
      setIsSubmitting(false)
    }
  }

  function handleKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()
      void submit()
    }
  }

  function handleFormSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    void submit()
  }

  return (
    <form onSubmit={handleFormSubmit} className="flex flex-col gap-2">
      <Label htmlFor={textareaId} className="sr-only">
        What do you do?
      </Label>
      <div className="flex items-end gap-2">
        <Textarea
          id={textareaId}
          value={value}
          onChange={(event) => setValue(event.target.value)}
          onKeyDown={handleKeyDown}
          disabled={isSubmitting}
          placeholder="What do you do?"
          rows={2}
          className="min-h-11 flex-1 resize-none"
          aria-invalid={errorMessage ? true : undefined}
          aria-describedby={errorMessage ? errorId : undefined}
        />
        <Button
          type="submit"
          disabled={isSubmitting || value.trim().length === 0}
          className="min-h-11 min-w-11"
        >
          {isSubmitting ? 'Sending…' : 'Send'}
        </Button>
      </div>
      {errorMessage && (
        <p id={errorId} role="alert" className="text-sm text-destructive">
          {errorMessage}
        </p>
      )}
    </form>
  )
}

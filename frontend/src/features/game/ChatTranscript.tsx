import { useEffect, useLayoutEffect, useRef } from 'react'

import { Message, MessageContent, MessageGroup } from '@/components/ui/message'
import { ScrollArea } from '@/components/ui/scroll-area'
import type { StoryMessage } from '@/features/setup/saves-api'

// Only auto-scroll to the newest message if the reader was already within
// this many pixels of the bottom - lets someone scroll up to reread earlier
// text without getting yanked back down by a new arrival.
const NEAR_BOTTOM_THRESHOLD_PX = 80

interface ChatTranscriptProps {
  messages: StoryMessage[]
  pending?: boolean
}

export function ChatTranscript({ messages, pending = false }: ChatTranscriptProps) {
  const viewportRef = useRef<HTMLDivElement>(null)
  const wasNearBottomRef = useRef(true)

  useEffect(() => {
    const viewport = viewportRef.current
    if (!viewport) return

    function handleScroll() {
      if (!viewport) return
      const distanceFromBottom =
        viewport.scrollHeight - viewport.scrollTop - viewport.clientHeight
      wasNearBottomRef.current = distanceFromBottom <= NEAR_BOTTOM_THRESHOLD_PX
    }

    viewport.addEventListener('scroll', handleScroll)
    return () => viewport.removeEventListener('scroll', handleScroll)
  }, [])

  useLayoutEffect(() => {
    const viewport = viewportRef.current
    if (viewport && wasNearBottomRef.current) {
      viewport.scrollTop = viewport.scrollHeight
    }
  }, [messages, pending])

  return (
    <ScrollArea viewportRef={viewportRef} className="h-full">
      <div
        role="log"
        aria-live="polite"
        aria-atomic="false"
        aria-busy={pending}
        className="flex flex-col gap-4 p-4"
      >
        <MessageGroup>
          {messages.map((message, index) => (
            <Message
              key={`${message.turn_number}-${message.role}-${index}`}
              align={message.role === 'player' ? 'end' : 'start'}
            >
              <MessageContent
                className={
                  message.role === 'player'
                    ? 'rounded-2xl bg-primary px-3 py-2 text-primary-foreground'
                    : 'rounded-2xl bg-muted px-3 py-2'
                }
              >
                {message.content}
              </MessageContent>
            </Message>
          ))}
        </MessageGroup>
        {pending && (
          <p className="px-3 text-sm text-muted-foreground">The narrator is composing a reply…</p>
        )}
      </div>
    </ScrollArea>
  )
}

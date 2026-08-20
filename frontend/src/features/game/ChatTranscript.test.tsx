import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import type { StoryMessage } from '@/features/setup/saves-api'

import { ChatTranscript } from './ChatTranscript'

function message(overrides: Partial<StoryMessage>): StoryMessage {
  return {
    role: 'narrator',
    content: 'Hello.',
    turn_number: 0,
    created_at: '2026-01-01T00:00:00Z',
    ...overrides,
  }
}

function getViewport(container: HTMLElement): HTMLDivElement {
  return container.querySelector('[data-slot="scroll-area-viewport"]') as HTMLDivElement
}

describe('ChatTranscript', () => {
  it('renders each message with role-appropriate alignment', () => {
    const messages = [
      message({ role: 'narrator', content: 'A cooking fire flares blue.', turn_number: 0 }),
      message({ role: 'player', content: 'I investigate.', turn_number: 1 }),
    ]

    render(<ChatTranscript messages={messages} />)

    const playerMessage = screen.getByText('I investigate.').closest('[data-slot="message"]')
    expect(playerMessage).toHaveAttribute('data-align', 'end')

    const narratorMessage = screen
      .getByText('A cooking fire flares blue.')
      .closest('[data-slot="message"]')
    expect(narratorMessage).toHaveAttribute('data-align', 'start')
  })

  it('exposes the required live-region accessibility attributes', () => {
    render(<ChatTranscript messages={[]} />)

    const log = screen.getByRole('log')
    expect(log).toHaveAttribute('aria-live', 'polite')
    expect(log).toHaveAttribute('aria-atomic', 'false')
    expect(log).toHaveAttribute('aria-busy', 'false')
  })

  it('marks the transcript busy while a turn is pending', () => {
    render(<ChatTranscript messages={[]} pending />)

    expect(screen.getByRole('log')).toHaveAttribute('aria-busy', 'true')
    expect(screen.getByText(/composing a reply/i)).toBeInTheDocument()
  })

  it('auto-scrolls to the newest message when the reader was already near the bottom', () => {
    const { container, rerender } = render(
      <ChatTranscript messages={[message({ content: 'One' })]} />
    )
    const viewport = getViewport(container)

    Object.defineProperty(viewport, 'scrollHeight', { value: 500, configurable: true })
    Object.defineProperty(viewport, 'clientHeight', { value: 420, configurable: true })
    viewport.scrollTop = 80 // exactly at the near-bottom threshold
    fireEvent.scroll(viewport)

    rerender(
      <ChatTranscript
        messages={[message({ content: 'One' }), message({ content: 'Two', turn_number: 1 })]}
      />
    )

    expect(viewport.scrollTop).toBe(500)
  })

  it('does not auto-scroll when the reader has scrolled away from the bottom', () => {
    const { container, rerender } = render(
      <ChatTranscript messages={[message({ content: 'One' })]} />
    )
    const viewport = getViewport(container)

    Object.defineProperty(viewport, 'scrollHeight', { value: 1000, configurable: true })
    Object.defineProperty(viewport, 'clientHeight', { value: 300, configurable: true })
    viewport.scrollTop = 0 // 700px from the bottom - well past the threshold
    fireEvent.scroll(viewport)

    rerender(
      <ChatTranscript
        messages={[message({ content: 'One' }), message({ content: 'Two', turn_number: 1 })]}
      />
    )

    expect(viewport.scrollTop).toBe(0)
  })
})

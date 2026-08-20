import { act, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { createRef } from 'react'
import { describe, expect, it, vi } from 'vitest'

import { Composer, type ComposerHandle } from './Composer'

function getTextarea() {
  return screen.getByLabelText('What do you do?')
}

describe('Composer', () => {
  it('submits the trimmed message on Enter and clears the textarea', async () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined)
    render(<Composer onSubmit={onSubmit} />)

    fireEvent.change(getTextarea(), { target: { value: '  I look around.  ' } })
    fireEvent.keyDown(getTextarea(), { key: 'Enter' })

    await waitFor(() => expect(onSubmit).toHaveBeenCalledWith('I look around.'))
    await waitFor(() => expect(getTextarea()).toHaveValue(''))
  })

  it('inserts a newline on Shift+Enter instead of submitting', () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined)
    render(<Composer onSubmit={onSubmit} />)

    fireEvent.change(getTextarea(), { target: { value: 'line one' } })
    fireEvent.keyDown(getTextarea(), { key: 'Enter', shiftKey: true })

    expect(onSubmit).not.toHaveBeenCalled()
  })

  it('does not submit an empty or whitespace-only message', () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined)
    render(<Composer onSubmit={onSubmit} />)

    fireEvent.change(getTextarea(), { target: { value: '   ' } })
    fireEvent.keyDown(getTextarea(), { key: 'Enter' })

    expect(onSubmit).not.toHaveBeenCalled()
    expect(screen.getByRole('button', { name: 'Send' })).toBeDisabled()
  })

  it('disables the textarea and button while a submission is in flight', async () => {
    let resolveSubmit!: () => void
    const onSubmit = vi.fn(
      () =>
        new Promise<void>((resolve) => {
          resolveSubmit = resolve
        })
    )
    render(<Composer onSubmit={onSubmit} />)

    fireEvent.change(getTextarea(), { target: { value: 'I wait.' } })
    fireEvent.keyDown(getTextarea(), { key: 'Enter' })

    await waitFor(() => expect(getTextarea()).toBeDisabled())
    expect(screen.getByRole('button', { name: 'Sending…' })).toBeDisabled()

    resolveSubmit()
    await waitFor(() => expect(getTextarea()).not.toBeDisabled())
  })

  it('preserves the typed message and allows retry when submission fails', async () => {
    const onSubmit = vi.fn().mockRejectedValue(new Error('network error'))
    render(<Composer onSubmit={onSubmit} errorMessage="Could not reach the narrator." />)

    fireEvent.change(getTextarea(), { target: { value: 'I try again.' } })
    fireEvent.keyDown(getTextarea(), { key: 'Enter' })

    await waitFor(() => expect(onSubmit).toHaveBeenCalledTimes(1))
    expect(getTextarea()).toHaveValue('I try again.')
    expect(getTextarea()).not.toBeDisabled()

    fireEvent.keyDown(getTextarea(), { key: 'Enter' })
    await waitFor(() => expect(onSubmit).toHaveBeenCalledTimes(2))
  })

  it('renders the error message in an alert region', () => {
    render(<Composer onSubmit={vi.fn()} errorMessage="Could not reach the narrator." />)

    expect(screen.getByRole('alert')).toHaveTextContent('Could not reach the narrator.')
  })

  it('exposes insertText via ref, appending to existing text and focusing the textarea', () => {
    const ref = createRef<ComposerHandle>()
    render(<Composer ref={ref} onSubmit={vi.fn()} />)

    fireEvent.change(getTextarea(), { target: { value: 'I look at the' } })
    act(() => ref.current?.insertText('Iron Cook Knife'))

    expect(getTextarea()).toHaveValue('I look at the Iron Cook Knife')
    expect(getTextarea()).toHaveFocus()
  })

  it('insertText on an empty textarea sets the text directly, with no leading space', () => {
    const ref = createRef<ComposerHandle>()
    render(<Composer ref={ref} onSubmit={vi.fn()} />)

    act(() => ref.current?.insertText('Ember Charm'))

    expect(getTextarea()).toHaveValue('Ember Charm')
  })
})

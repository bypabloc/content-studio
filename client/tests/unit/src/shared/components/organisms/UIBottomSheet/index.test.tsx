import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { useState } from 'react'
import { describe, expect, it, vi } from 'vitest'

import { UIBottomSheet } from '@/shared/components/organisms/UIBottomSheet'

describe('UIBottomSheet [AC-1, AC-21]', () => {
  it('WHEN open THEN renders a named modal with a 44 px close button', () => {
    render(<UIBottomSheet open onOpenChange={vi.fn()} title="More options" closeLabel="Close" sections={[<p key="one">First section</p>]} />)

    expect(screen.getByRole('dialog', { name: 'More options' })).toBeTruthy()
    expect(screen.getByRole('heading', { level: 2, name: 'More options' })).toBeTruthy()
    expect(screen.getByRole('button', { name: 'Close' }).getAttribute('class')).toContain('size-11')
  })

  it('WHEN Escape is pressed THEN requests closing and restores focus to the trigger', async () => {
    const user = userEvent.setup()
    const onOpenChange = vi.fn()
    function Harness(): React.JSX.Element {
      const [open, setOpen] = useState(false)
      return (
        <>
          <button type="button" onClick={() => setOpen(true)}>Open options</button>
          <UIBottomSheet open={open} onOpenChange={(nextOpen) => { onOpenChange(nextOpen); setOpen(nextOpen) }} title="More options" closeLabel="Close" sections={[]} />
        </>
      )
    }
    render(
      <Harness />,
    )
    const trigger = screen.getByRole('button', { name: 'Open options' })
    await user.click(trigger)
    await screen.findByRole('dialog', { name: 'More options' })

    await user.keyboard('{Escape}')

    expect(onOpenChange).toHaveBeenCalledWith(false)
    await waitFor(() => expect(document.activeElement).toBe(trigger))
  })

  it('WHEN the sheet closes THEN reports completion after the exit transition', async () => {
    const user = userEvent.setup()
    const onOpenChangeComplete = vi.fn()
    const { rerender } = render(<UIBottomSheet open onOpenChange={vi.fn()} onOpenChangeComplete={onOpenChangeComplete} title="More options" closeLabel="Close" sections={[]} />)

    await user.click(screen.getByRole('button', { name: 'Close' }))
    rerender(<UIBottomSheet open={false} onOpenChange={vi.fn()} onOpenChangeComplete={onOpenChangeComplete} title="More options" closeLabel="Close" sections={[]} />)

    await waitFor(() => expect(onOpenChangeComplete).toHaveBeenCalledWith(false))
  })

  it('WHEN multiple sections are provided THEN separates them with a top border', () => {
    render(
      <UIBottomSheet
        open
        onOpenChange={vi.fn()}
        title="More options"
        description="Available sections"
        closeLabel="Close"
        sections={[<p key="one">Identity</p>, <p key="two">Destinations</p>]}
      />,
    )
    const sections = document.querySelectorAll('[data-slot="bottom-sheet-section"]')

    expect(screen.getByText('Available sections')).toBeTruthy()
    expect(sections).toHaveLength(2)
    expect(sections[1].getAttribute('class')).toContain('border-t')
  })
})

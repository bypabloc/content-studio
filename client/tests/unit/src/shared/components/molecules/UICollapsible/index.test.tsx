import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'

import { UICollapsible } from '@/shared/components/molecules/UICollapsible'

const PANEL_CLASSES = [
  'h-(--collapsible-panel-height)',
  'overflow-hidden',
  'transition-[height]',
  'duration-150',
  'ease-ui-out',
  'motion-reduce:transition-none',
  'data-starting-style:h-0',
  'data-ending-style:h-0',
  'motion-safe:animate-ui-fade',
]

describe('UICollapsible', () => {
  it('WHEN closed by default and pressed THEN opens the content', async () => {
    const user = userEvent.setup()
    render(<UICollapsible trigger="How to read it">Taller bars, more sales.</UICollapsible>)

    const trigger = screen.getByRole('button', { name: 'How to read it' })
    expect(trigger.getAttribute('aria-expanded')).toBe('false')
    expect(trigger.className).toContain('min-h-11')
    // Junto a otra acción (p. ej. «Ver datos») el disparador no se parte en dos líneas.
    expect(trigger.className).toContain('whitespace-nowrap')
    expect(screen.queryByText('Taller bars, more sales.')).toBeNull()

    await user.click(trigger)

    expect(await screen.findByText('Taller bars, more sales.')).toBeTruthy()
    expect(trigger.getAttribute('aria-expanded')).toBe('true')
  })

  it('WHEN defaultOpen THEN starts open', () => {
    render(
      <UICollapsible trigger="Help" defaultOpen>
        text
      </UICollapsible>,
    )

    expect(screen.getByText('text')).toBeTruthy()
  })

  it('WHEN the collapsible opens THEN its panel has the height, starting and ending styles and the fade class [AC-7]', async () => {
    const user = userEvent.setup()
    render(<UICollapsible trigger="How to read it">Taller bars, more sales.</UICollapsible>)

    await user.click(screen.getByRole('button', { name: 'How to read it' }))
    await screen.findByText('Taller bars, more sales.')

    const panel = document.querySelector<HTMLElement>('[data-slot="collapsible-content"]')
    if (!panel) throw new Error('collapsible panel is not mounted')
    for (const name of PANEL_CLASSES) expect(panel.classList.contains(name)).toBe(true)
  })
})

import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { useRef, useState } from 'react'
import { describe, expect, it, vi } from 'vitest'

import { UIPopover } from '@/shared/components/molecules/UIPopover'

function Demo(): React.JSX.Element {
  const [open, setOpen] = useState(false)
  const anchor = useRef<HTMLButtonElement>(null)

  return (
    <>
      <button ref={anchor} type="button" onClick={() => setOpen(true)}>
        Open notifications
      </button>
      <UIPopover anchor={anchor} open={open} onOpenChange={setOpen} label="Notifications">
        Notification panel
      </UIPopover>
    </>
  )
}

describe('UIPopover [AC-28]', () => {
  it('WHEN the anchor button is activated THEN the panel opens with its accessible label [AC-28]', async () => {
    const user = userEvent.setup()
    render(<Demo />)

    await user.click(screen.getByRole('button', { name: 'Open notifications' }))

    expect(await screen.findByRole('dialog', { name: 'Notifications' })).toBeTruthy()
    expect(screen.getByText('Notification panel')).toBeTruthy()
  })

  it('WHEN Escape is pressed THEN the panel closes and focus returns to the anchor button [AC-28]', async () => {
    const user = userEvent.setup()
    render(<Demo />)
    const anchor = screen.getByRole('button', { name: 'Open notifications' })

    await user.click(anchor)
    await screen.findByRole('dialog', { name: 'Notifications' })
    await user.keyboard('{Escape}')

    await waitFor(() => expect(screen.queryByRole('dialog', { name: 'Notifications' })).toBeNull(), { timeout: 5000 })
    await waitFor(() => expect(document.activeElement).toBe(anchor), { timeout: 5000 })
  })

  it('WHEN side and align are given THEN the panel opens there and never grows past the available viewport', async () => {
    const anchor = { current: document.createElement('button') }
    document.body.append(anchor.current)
    render(
      <UIPopover anchor={anchor} open onOpenChange={() => undefined} label="Report" side="top" align="end">
        Report panel
      </UIPopover>,
    )

    const panel = await screen.findByRole('dialog', { name: 'Report' })
    expect(panel.getAttribute('data-side')).toBe('top')
    expect(panel.getAttribute('data-align')).toBe('end')
    expect(panel.className).toContain('max-h-(--available-height)')
    expect(panel.className).toContain('overflow-y-auto')
    anchor.current.remove()
  })

  it('WHEN side is given THEN the panel keeps that side and only the available height limits it', async () => {
    const seen: unknown[] = []
    vi.resetModules()
    vi.doMock('@/shared/components/shadcn/popover', () => ({
      Popover: ({ children }: { children: React.ReactNode }) => children,
      PopoverContent: ({ collisionAvoidance, children }: { collisionAvoidance?: unknown; children: React.ReactNode }) => {
        seen.push(collisionAvoidance)
        return children
      },
    }))
    const { UIPopover: Mocked } = await import('@/shared/components/molecules/UIPopover')
    const anchor = { current: document.createElement('button') }

    const { rerender } = render(<Mocked anchor={anchor} open onOpenChange={() => undefined} label="Report" side="bottom">x</Mocked>)
    rerender(<Mocked anchor={anchor} open onOpenChange={() => undefined} label="Report">x</Mocked>)

    expect(seen).toEqual([{ side: 'none' }, undefined])
    vi.doUnmock('@/shared/components/shadcn/popover')
    vi.resetModules()
  })

  it('WHEN open is controlled to false THEN the panel content is not rendered [AC-28]', () => {
    const anchor = { current: document.createElement('button') }
    render(
      <UIPopover anchor={anchor} open={false} onOpenChange={() => undefined} label="Notifications">
        Hidden notification panel
      </UIPopover>,
    )

    expect(screen.queryByText('Hidden notification panel')).toBeNull()
  })
})

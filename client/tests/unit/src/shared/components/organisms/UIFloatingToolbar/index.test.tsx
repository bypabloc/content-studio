import { act, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { useState } from 'react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { UIFloatingToolbar, type FloatingToolbarPlacement } from '@/shared/components/organisms/UIFloatingToolbar'

const ITEMS = [
  { id: 'headers', label: 'Headers', icon: 'shield-alert' as const },
  { id: 'network', label: 'Network', icon: 'clipboard-list' as const, separatorBefore: true },
  { id: 'settings', label: 'Settings', icon: 'settings' as const, separatorBefore: true },
]

type DemoProps = {
  placement?: FloatingToolbarPlacement
  bottomNavOffset?: boolean
  autoHide?: boolean
  notice?: string
  onChange?: (id: string | null) => void
}

function Demo({ placement = 'bottom', bottomNavOffset = false, autoHide = false, notice, onChange }: DemoProps): React.JSX.Element {
  const [activeId, setActiveId] = useState<string | null>(null)
  const items = ITEMS.map((item) => item.id === 'network' && notice ? { ...item, notice } : item)

  function handleActiveChange(id: string | null): void {
    onChange?.(id)
    setActiveId(id)
  }

  return (
    <main>
      <button type="button">Outside</button>
      <UIFloatingToolbar
        label="Development tools"
        showLabel="Show development tools"
        closeLabel={(tool) => `Close ${tool}`}
        items={items}
        placement={placement}
        bottomNavOffset={bottomNavOffset}
        autoHide={autoHide}
        activeId={activeId}
        onActiveChange={handleActiveChange}
      >
        <section>Tool panel</section>
      </UIFloatingToolbar>
    </main>
  )
}

const PLACEMENTS: Array<{
  placement: FloatingToolbarPlacement
  orientation: 'horizontal' | 'vertical'
  rootClass: string
  hiddenClass: string
  side: 'top' | 'right' | 'bottom' | 'left'
  align: 'start' | 'center' | 'end'
}> = [
  { placement: 'top-left', orientation: 'horizontal', rootClass: 'top-4 left-4', hiddenClass: '-translate-y-[calc(100%+1rem)]', side: 'bottom', align: 'start' },
  { placement: 'top', orientation: 'horizontal', rootClass: 'top-4 left-1/2', hiddenClass: '-translate-y-[calc(100%+1rem)]', side: 'bottom', align: 'center' },
  { placement: 'top-right', orientation: 'horizontal', rootClass: 'top-4 right-4', hiddenClass: '-translate-y-[calc(100%+1rem)]', side: 'bottom', align: 'end' },
  { placement: 'left', orientation: 'vertical', rootClass: 'left-4 top-1/2', hiddenClass: '-translate-x-[calc(100%+1rem)]', side: 'right', align: 'center' },
  { placement: 'right', orientation: 'vertical', rootClass: 'right-4 top-1/2', hiddenClass: 'translate-x-[calc(100%+1rem)]', side: 'left', align: 'center' },
  { placement: 'bottom-left', orientation: 'horizontal', rootClass: 'bottom-4 left-4', hiddenClass: 'translate-y-[calc(100%+1rem)]', side: 'top', align: 'start' },
  { placement: 'bottom', orientation: 'horizontal', rootClass: 'bottom-4 left-1/2', hiddenClass: 'translate-y-[calc(100%+1rem)]', side: 'top', align: 'center' },
  { placement: 'bottom-right', orientation: 'horizontal', rootClass: 'bottom-4 right-4', hiddenClass: 'translate-y-[calc(100%+1rem)]', side: 'top', align: 'end' },
]

describe('UIFloatingToolbar', () => {
  beforeEach(() => {
    vi.useFakeTimers({ shouldAdvanceTime: true })
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it.each(PLACEMENTS)('WHEN placed at $placement THEN it has the matching toolbar orientation and popup position [AC-11, AC-12, AC-14]', async ({ placement, orientation, rootClass, side, align }) => {
    const user = userEvent.setup()
    const { unmount } = render(<Demo placement={placement} />)
    const toolbar = screen.getByRole('toolbar', { name: 'Development tools' })

    expect(toolbar.getAttribute('aria-orientation')).toBe(orientation)
    expect(toolbar.parentElement?.className).toContain(rootClass)
    expect(screen.getAllByRole('separator')).toHaveLength(2)

    await user.click(screen.getByRole('button', { name: 'Headers' }))
    const dialog = await screen.findByRole('dialog', { name: 'Headers' })
    expect(dialog.getAttribute('data-side')).toBe(side)
    expect(dialog.getAttribute('data-align')).toBe(align)
    unmount()
  })

  it('WHEN bottomNavOffset is enabled THEN bottom placements clear the navigation bar', () => {
    const { rerender } = render(<Demo placement="bottom" bottomNavOffset />)
    expect(screen.getByRole('toolbar', { name: 'Development tools' }).parentElement?.className)
      .toContain('bottom-[calc(1rem+var(--ui-bottom-nav-offset))]')

    rerender(<Demo placement="top" bottomNavOffset />)
    expect(screen.getByRole('toolbar', { name: 'Development tools' }).parentElement?.className).toContain('top-4')
  })

  it.each(['left', 'right'] as const)('WHEN the toolbar is vertical at %s THEN the popup is width-limited on small screens [AC-12]', async (placement) => {
    const user = userEvent.setup()
    render(<Demo placement={placement} />)

    await user.click(screen.getByRole('button', { name: 'Headers' }))

    const dialog = await screen.findByRole('dialog', { name: 'Headers' })
    expect(dialog.className).toContain('max-sm:max-w-[calc(100vw-5rem)]')
  })

  it('WHEN the toolbar receives ArrowRight THEN focus moves to the next tool [AC-11]', async () => {
    const user = userEvent.setup()
    render(<Demo />)
    const headers = screen.getByRole('button', { name: 'Headers' })
    const network = screen.getByRole('button', { name: 'Network' })

    headers.focus()
    await user.keyboard('{ArrowRight}')

    expect(document.activeElement).toBe(network)
  })

  it('WHEN a tool is hovered for 200 ms THEN its tooltip appears [AC-11]', async () => {
    const user = userEvent.setup()
    render(<Demo />)

    await user.hover(screen.getByRole('button', { name: 'Headers' }))
    await act(async () => vi.advanceTimersByTimeAsync(200))

    expect(screen.getByRole('tooltip').textContent).toContain('Headers')
  })

  it('WHEN an item has a notice THEN the button announces it and renders a decorative status dot [AC-18]', () => {
    render(<Demo notice="unreviewed error responses" />)
    const network = screen.getByRole('button', { name: 'Network, unreviewed error responses' })

    expect(network.getAttribute('aria-haspopup')).toBe('dialog')
    expect(network.querySelector('span[aria-hidden="true"]')).not.toBeNull()
  })

  it('WHEN a tool is activated THEN its dialog opens and the active tool can close it [AC-13]', async () => {
    const user = userEvent.setup()
    const onChange = vi.fn()
    render(<Demo onChange={onChange} />)
    const headers = screen.getByRole('button', { name: 'Headers' })

    await user.click(headers)

    expect(onChange).toHaveBeenLastCalledWith('headers')
    expect(headers.getAttribute('aria-expanded')).toBe('true')
    const dialog = await screen.findByRole('dialog', { name: 'Headers' })
    expect(dialog.contains(screen.getByText('Tool panel'))).toBe(true)
    expect(document.activeElement).toBe(dialog.querySelector('[role="heading"][aria-level="2"]'))
    expect(screen.queryByRole('tooltip')).toBeNull()

    await user.click(headers)
    await waitFor(() => expect(screen.queryByRole('dialog', { name: 'Headers' })).toBeNull())
    expect(onChange).toHaveBeenLastCalledWith(null)
  })

  it('WHEN the close button is pressed THEN it closes the active dialog [AC-13]', async () => {
    const user = userEvent.setup()
    render(<Demo />)
    await user.click(screen.getByRole('button', { name: 'Headers' }))
    await screen.findByRole('dialog', { name: 'Headers' })

    await user.click(screen.getByRole('button', { name: 'Close Headers' }))

    await waitFor(() => expect(screen.queryByRole('dialog', { name: 'Headers' })).toBeNull())
  })

  it('WHEN Escape closes a tool THEN focus returns to its toolbar button [AC-13]', async () => {
    const user = userEvent.setup()
    render(<Demo />)
    const headers = screen.getByRole('button', { name: 'Headers' })
    await user.click(headers)
    await screen.findByRole('dialog', { name: 'Headers' })

    await user.keyboard('{Escape}')

    await waitFor(() => expect(screen.queryByRole('dialog', { name: 'Headers' })).toBeNull())
    await waitFor(() => expect(document.activeElement).toBe(headers))
  })

  it('WHEN a pointer press happens outside the toolbar THEN the active tool stays open [AC-13]', async () => {
    const user = userEvent.setup()
    const onChange = vi.fn()
    render(<Demo onChange={onChange} />)
    await user.click(screen.getByRole('button', { name: 'Headers' }))
    await screen.findByRole('dialog', { name: 'Headers' })
    onChange.mockClear()

    fireEvent.pointerDown(screen.getByRole('button', { name: 'Outside' }))

    expect(screen.getByRole('dialog', { name: 'Headers' })).not.toBeNull()
    expect(onChange).not.toHaveBeenCalled()
  })

  it('WHEN auto-hide reaches 1999 ms THEN the toolbar is visible; at 2000 ms it leaves an accessible handle [AC-15]', async () => {
    // Reloj falso puro: con shouldAdvanceTime el tiempo real de una máquina cargada cruza el borde de 1999 ms.
    vi.useRealTimers()
    vi.useFakeTimers()
    render(<Demo autoHide />)
    const toolbar = screen.getByRole('toolbar', { name: 'Development tools' })

    await act(async () => vi.advanceTimersByTimeAsync(1999))
    expect(toolbar.hasAttribute('inert')).toBe(false)
    expect(screen.queryByRole('button', { name: 'Show development tools' })).toBeNull()

    await act(async () => vi.advanceTimersByTimeAsync(1))
    expect(toolbar.hasAttribute('inert')).toBe(true)
    expect(toolbar.className).toContain('translate-y-[calc(100%+1rem)]')
    expect(screen.getByRole('button', { name: 'Show development tools' })).not.toBeNull()
  })

  it.each(['pointerEnter', 'focus', 'click'] as const)('WHEN the hidden handle receives %s THEN the toolbar is shown [AC-15]', async (eventName) => {
    render(<Demo autoHide />)
    await act(async () => vi.advanceTimersByTimeAsync(2000))
    const handle = screen.getByRole('button', { name: 'Show development tools' })

    if (eventName === 'pointerEnter') fireEvent.pointerEnter(handle)
    if (eventName === 'focus') fireEvent.focus(handle)
    if (eventName === 'click') fireEvent.click(handle)

    expect(screen.getByRole('toolbar', { name: 'Development tools' }).hasAttribute('inert')).toBe(false)
    expect(screen.queryByRole('button', { name: 'Show development tools' })).toBeNull()
    if (eventName !== 'pointerEnter') {
      expect(document.activeElement).toBe(screen.getByRole('button', { name: 'Headers' }))
    }
  })

  it('WHEN the pointer enters the toolbar THEN the pending auto-hide is cancelled [AC-15]', async () => {
    render(<Demo autoHide />)
    const toolbar = screen.getByRole('toolbar', { name: 'Development tools' })

    fireEvent.pointerEnter(toolbar)
    await act(async () => vi.advanceTimersByTimeAsync(5000))

    expect(toolbar.hasAttribute('inert')).toBe(false)
  })

  it('WHEN focus leaves the toolbar THEN it hides after the delay; moving focus within it keeps it visible [AC-15]', async () => {
    render(<Demo autoHide />)
    const headers = screen.getByRole('button', { name: 'Headers' })
    const network = screen.getByRole('button', { name: 'Network' })
    headers.focus()
    fireEvent.blur(headers, { relatedTarget: network })
    await act(async () => vi.advanceTimersByTimeAsync(2000))
    expect(screen.getByRole('toolbar', { name: 'Development tools' }).hasAttribute('inert')).toBe(false)

    fireEvent.blur(network, { relatedTarget: screen.getByRole('button', { name: 'Outside' }) })
    await act(async () => vi.advanceTimersByTimeAsync(2000))
    expect(screen.getByRole('toolbar', { name: 'Development tools' }).hasAttribute('inert')).toBe(true)
  })

  it('WHEN Escape is pressed while the toolbar has focus and no tool is active THEN the toolbar hides [AC-15]', async () => {
    const user = userEvent.setup()
    render(<Demo autoHide />)
    const headers = screen.getByRole('button', { name: 'Headers' })
    headers.focus()
    await user.keyboard('{Escape}')

    expect(screen.getByRole('toolbar', { name: 'Development tools' }).hasAttribute('inert')).toBe(true)
  })

  it.each([
    { autoHide: false, activate: false },
    { autoHide: true, activate: true },
  ])('WHEN auto-hide is disabled or a tool is open THEN the toolbar remains visible after 10 seconds [AC-16]', async ({ autoHide, activate }) => {
    const user = userEvent.setup()
    render(<Demo autoHide={autoHide} />)
    if (activate) await user.click(screen.getByRole('button', { name: 'Headers' }))
    const toolbar = screen.getByRole('toolbar', { name: 'Development tools' })

    await act(async () => vi.advanceTimersByTimeAsync(10_000))

    expect(toolbar.hasAttribute('inert')).toBe(false)
  })

  it('WHEN a tool panel is open THEN it has an opaque card background, fits the viewport and masks the page edges around it on narrow screens [AC-20]', async () => {
    const user = userEvent.setup()
    render(<Demo />)
    await user.click(screen.getByRole('button', { name: 'Headers' }))

    const dialog = await screen.findByRole('dialog', { name: 'Headers' })
    expect(dialog.className).toContain('bg-card')
    expect(dialog.className).toContain('border-border')
    expect(dialog.className).toContain('w-[min(40rem,calc(100vw-2rem))]')
    expect(dialog.className).toContain('max-h-[min(30rem,calc(100dvh-8rem))]')
    expect(dialog.className).toContain('max-sm:ring-8')
    expect(dialog.className).toContain('max-sm:ring-background')
    expect(dialog.className).toContain('max-sm:shadow-none')
    expect(dialog.className).not.toMatch(/bg-(?:card|popover)\//)
  })

  it('WHEN a tool panel is open THEN its title stays outside the scrolling body [AC-16, AC-20]', async () => {
    const user = userEvent.setup()
    render(<Demo />)
    await user.click(screen.getByRole('button', { name: 'Headers' }))

    const dialog = await screen.findByRole('dialog', { name: 'Headers' })
    const title = within(dialog).getByRole('heading', { name: 'Headers' })
    const body = within(dialog).getByText('Tool panel')
    expect(title.closest('.overflow-y-auto')).toBeNull()
    expect(body.closest('.overflow-y-auto')).not.toBeNull()
  })

  it('WHEN a tool panel is open THEN the toolbar drops its card surface on narrow screens so it does not read as a second card [AC-16]', async () => {
    const user = userEvent.setup()
    render(<Demo />)
    const toolbar = screen.getByRole('toolbar', { name: 'Development tools' })
    expect(toolbar.className).not.toContain('max-sm:bg-transparent')

    await user.click(screen.getByRole('button', { name: 'Headers' }))
    expect(toolbar.className).toContain('max-sm:border-transparent')
    expect(toolbar.className).toContain('max-sm:bg-transparent')
    expect(toolbar.className).toContain('max-sm:shadow-none')

    await user.click(screen.getByRole('button', { name: 'Close Headers' }))
    expect(toolbar.className).not.toContain('max-sm:bg-transparent')
  })

  it('WHEN motion preferences are applied THEN toolbar transitions honor reduced motion and use theme tokens [AC-17, AC-19]', () => {
    render(<Demo />)
    const toolbar = screen.getByRole('toolbar', { name: 'Development tools' })
    const classes = toolbar.className

    expect(classes).toContain('motion-safe:transition-transform')
    expect(classes).toContain('motion-reduce:transition-none')
    expect(classes).not.toMatch(/(?:bg|text|border)-\[#/)
  })
})

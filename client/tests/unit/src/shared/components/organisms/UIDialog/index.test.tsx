import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { useRef, useState } from 'react'
import { describe, expect, it } from 'vitest'

import { UIDialog } from '@/shared/components/organisms/UIDialog'

function Demo(): React.JSX.Element {
  const [open, setOpen] = useState(false)
  return (
    <>
      <button type="button" onClick={() => setOpen(true)}>
        open
      </button>
      <UIDialog open={open} onOpenChange={setOpen} title="New user" description="Fill in the data" closeLabel="Close" footer={<span>footer</span>}>
        <input aria-label="name" />
      </UIDialog>
    </>
  )
}

describe('UIDialog [AC-9]', () => {
  it('WHEN opened THEN dialog with title and description, and Escape closes it', async () => {
    const user = userEvent.setup()
    render(<Demo />)

    await user.click(screen.getByRole('button', { name: 'open' }))
    const dialog = await screen.findByRole('dialog', { name: 'New user' })
    expect(dialog.textContent).toContain('Fill in the data')
    expect(screen.getByText('footer')).toBeTruthy()
    await user.keyboard('{Escape}')

    await waitFor(() => expect(screen.queryByRole('dialog')).toBeNull(), { timeout: 5000 })
  })

  it('WHEN the close button is used THEN it closes', async () => {
    const user = userEvent.setup()
    render(<Demo />)

    await user.click(screen.getByRole('button', { name: 'open' }))
    await user.click(await screen.findByRole('button', { name: 'Close' }))

    await waitFor(() => expect(screen.queryByRole('dialog')).toBeNull(), { timeout: 5000 })
  })

  it('WHEN there is no description or footer THEN only title and content', async () => {
    render(
      <UIDialog open onOpenChange={() => undefined} title="Password" closeLabel="Close">
        content
      </UIDialog>,
    )

    const dialog = await screen.findByRole('dialog', { name: 'Password' })
    expect(dialog.getAttribute('aria-describedby')).toBeNull()
    expect(dialog.querySelector('[data-slot="dialog-footer"]')).toBeNull()
  })

  it('WHEN modal is false THEN the dialog leaves the page interactive without an overlay', async () => {
    const user = userEvent.setup()
    let outsideClicks = 0
    render(
      <>
        <button type="button" onClick={() => outsideClicks++}>
          outside
        </button>
        <UIDialog open modal={false} onOpenChange={() => undefined} title="Tools" closeLabel="Close">
          tools
        </UIDialog>
      </>,
    )

    await screen.findByRole('dialog', { name: 'Tools' })
    expect(document.querySelector('[data-slot="dialog-overlay"]')).toBeNull()
    await user.click(screen.getByRole('button', { name: 'outside' }))
    expect(outsideClicks).toBe(1)
  })

  it('WHEN finalFocus is given THEN on close the focus returns to that element [AC-5]', async () => {
    function WithFocus(): React.JSX.Element {
      const [open, setOpen] = useState(false)
      const destination = useRef<HTMLButtonElement>(null)
      return (
        <>
          <button type="button" onClick={() => setOpen(true)}>
            open
          </button>
          <button type="button" ref={destination}>
            destination
          </button>
          <UIDialog open={open} onOpenChange={setOpen} title="Tooth" closeLabel="Close" finalFocus={destination}>
            content
          </UIDialog>
        </>
      )
    }
    const user = userEvent.setup()
    render(<WithFocus />)

    await user.click(screen.getByRole('button', { name: 'open' }))
    await screen.findByRole('dialog', { name: 'Tooth' })
    await user.keyboard('{Escape}')

    await waitFor(() => expect(document.activeElement).toBe(screen.getByRole('button', { name: 'destination' })), { timeout: 5000 })
  })
})

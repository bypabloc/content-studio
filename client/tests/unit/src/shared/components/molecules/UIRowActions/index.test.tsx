import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { UIRowActions } from '@/shared/components/molecules/UIRowActions'

describe('UIRowActions [AC-9]', () => {
  it('WHEN an action carries a typed analytics id THEN its menu item forwards it', async () => {
    const user = userEvent.setup()
    render(
      <UIRowActions
        label="Actions for Ana Ruiz"
        items={[{ key: 'deactivate', label: 'Deactivate', icon: 'user-x', analyticsId: 'users.deactivate', onSelect: vi.fn() }]}
      />,
    )

    await user.click(screen.getByRole('button', { name: 'Actions for Ana Ruiz' }))
    expect((await screen.findByRole('menuitem', { name: 'Deactivate' })).getAttribute('data-analytics')).toBe('users.deactivate')
  })

  it('WHEN opened THEN actions with their name; a disabled one explains why', async () => {
    const user = userEvent.setup()
    const edit = vi.fn()
    const deactivate = vi.fn()
    render(
      <UIRowActions
        label="Actions for Ana Ruiz"
        items={[
          { key: 'edit', label: 'Edit', icon: 'pencil', onSelect: edit },
          { key: 'deactivate', label: 'Deactivate', icon: 'user-x', destructive: true, disabled: true, disabledReason: 'You cannot deactivate yourself', onSelect: deactivate },
        ]}
      />,
    )

    await user.click(screen.getByRole('button', { name: 'Actions for Ana Ruiz' }))
    const deactivateItem = await screen.findByRole('menuitem', { name: (name) => name.includes('Deactivate') })
    expect(deactivateItem.getAttribute('aria-disabled')).toBe('true')
    expect(deactivateItem.textContent).toContain('You cannot deactivate yourself')
    await user.click(screen.getByRole('menuitem', { name: 'Edit' }))

    expect(edit).toHaveBeenCalledOnce()
    expect(deactivate).not.toHaveBeenCalled()
  })
})

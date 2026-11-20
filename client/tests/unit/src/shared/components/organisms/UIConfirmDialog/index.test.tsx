import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { UIConfirmDialog } from '@/shared/components/organisms/UIConfirmDialog'

const props = {
  triggerLabel: 'Cerrar todas',
  title: '¿Cerrar todas las sesiones?',
  description: 'Tendrás que volver a ingresar.',
  confirmLabel: 'Sí, cerrar',
  cancelLabel: 'Cancelar',
}

describe('UIConfirmDialog [AC-8]', () => {
  it('WHEN cancelled THEN does not confirm and focus returns to the trigger', async () => {
    const user = userEvent.setup()
    const onConfirm = vi.fn()
    render(<UIConfirmDialog {...props} onConfirm={onConfirm} />)
    const trigger = screen.getByRole('button', { name: 'Cerrar todas' })

    await user.click(trigger)
    await screen.findByRole('alertdialog', { name: '¿Cerrar todas las sesiones?' })
    await user.click(screen.getByRole('button', { name: 'Cancelar' }))

    await waitFor(() => expect(document.activeElement).toBe(trigger), { timeout: 5000 })
    expect(onConfirm).not.toHaveBeenCalled()
  })

  it('WHEN confirmed THEN calls onConfirm; pending keeps the action busy', async () => {
    const user = userEvent.setup()
    const onConfirm = vi.fn()
    const { rerender } = render(<UIConfirmDialog {...props} destructive onConfirm={onConfirm} />)

    await user.click(screen.getByRole('button', { name: 'Cerrar todas' }))
    await user.click(await screen.findByRole('button', { name: 'Sí, cerrar' }))
    expect(onConfirm).toHaveBeenCalledOnce()

    rerender(<UIConfirmDialog {...props} destructive pending onConfirm={onConfirm} />)
    expect(screen.getByRole('button', { name: 'Cerrar todas' }).getAttribute('aria-busy')).toBe('true')
  })

  it('WHEN controlled without trigger THEN opens by prop and notifies on close', async () => {
    const user = userEvent.setup()
    const onOpenChange = vi.fn()
    const onConfirm = vi.fn()
    const { triggerLabel: _, ...withoutTrigger } = props
    render(<UIConfirmDialog {...withoutTrigger} open onOpenChange={onOpenChange} onConfirm={onConfirm} />)

    await screen.findByRole('alertdialog', { name: '¿Cerrar todas las sesiones?' })
    expect(screen.queryByRole('button', { name: 'Cerrar todas' })).toBeNull()
    await user.click(screen.getByRole('button', { name: 'Sí, cerrar' }))

    expect(onConfirm).toHaveBeenCalledOnce()
    expect(onOpenChange).toHaveBeenCalledWith(false)
  })
})

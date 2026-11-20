import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { UIFormDialog } from '@/shared/components/organisms/UIFormDialog'

const props = {
  title: 'Invitar usuario',
  description: 'Recibirá un correo con el enlace de activación.',
  confirmLabel: 'Invitar',
  cancelLabel: 'Cancelar',
}

describe('UIFormDialog [AC-29]', () => {
  it('WHEN open THEN shows the fields inside a named dialog [AC-29]', async () => {
    render(
      <UIFormDialog {...props} open onOpenChange={vi.fn()} onSubmit={vi.fn()}>
        <input aria-label="Correo" />
      </UIFormDialog>,
    )

    await screen.findByRole('alertdialog', { name: 'Invitar usuario' })
    expect(screen.getByLabelText('Correo')).toBeTruthy()
  })

  it('WHEN confirmed THEN submits the form once and leaves closing to the caller [AC-29]', async () => {
    const user = userEvent.setup()
    const onOpenChange = vi.fn()
    const onSubmit = vi.fn()
    render(
      <UIFormDialog {...props} open onOpenChange={onOpenChange} onSubmit={onSubmit}>
        <input aria-label="Correo" />
      </UIFormDialog>,
    )

    await user.click(await screen.findByRole('button', { name: 'Invitar' }))

    expect(onSubmit).toHaveBeenCalledOnce()
    expect(onOpenChange).not.toHaveBeenCalled()
  })

  it('WHEN pending THEN the confirm action is disabled and busy [AC-29]', async () => {
    render(
      <UIFormDialog {...props} open pending onOpenChange={vi.fn()} onSubmit={vi.fn()}>
        <input aria-label="Correo" />
      </UIFormDialog>,
    )

    const confirm = await screen.findByRole('button', { name: 'Invitar' })
    expect(confirm.getAttribute('aria-busy')).toBe('true')
    expect((confirm as HTMLButtonElement).disabled).toBe(true)
  })

  it('WHEN confirm is disabled THEN it cannot submit the form', async () => {
    const onSubmit = vi.fn()
    render(
      <UIFormDialog {...props} open confirmDisabled onOpenChange={vi.fn()} onSubmit={onSubmit}>
        <input aria-label="Correo" />
      </UIFormDialog>,
    )

    const confirm = await screen.findByRole<HTMLButtonElement>('button', { name: 'Invitar' })
    expect(confirm.disabled).toBe(true)
    await userEvent.setup().click(confirm)
    expect(onSubmit).not.toHaveBeenCalled()
  })

  it('WHEN destructive THEN the confirm action uses the danger style [AC-29]', async () => {
    render(
      <UIFormDialog {...props} open destructive onOpenChange={vi.fn()} onSubmit={vi.fn()}>
        <input aria-label="Correo" />
      </UIFormDialog>,
    )

    const confirm = await screen.findByRole('button', { name: 'Invitar' })
    expect(confirm.className).toContain('bg-destructive')
  })

  it('WHEN cancelled THEN closes without submitting [AC-29]', async () => {
    const user = userEvent.setup()
    const onOpenChange = vi.fn()
    const onSubmit = vi.fn()
    render(
      <UIFormDialog {...props} open onOpenChange={onOpenChange} onSubmit={onSubmit}>
        <input aria-label="Correo" />
      </UIFormDialog>,
    )

    await user.click(await screen.findByRole('button', { name: 'Cancelar' }))

    expect(onOpenChange).toHaveBeenCalledWith(false)
    expect(onSubmit).not.toHaveBeenCalled()
  })
})

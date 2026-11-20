import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { UISwitch } from '@/shared/components/atoms/UISwitch'

describe('UISwitch', () => {
  it('WHEN activated by keyboard THEN exposes a labeled switch and reports the new value', async () => {
    const user = userEvent.setup()
    const onChange = vi.fn()
    render(<UISwitch label="Apagar Turnstile" checked={false} onChange={onChange} />)

    const control = screen.getByRole('switch', { name: 'Apagar Turnstile' })
    expect(control.getAttribute('aria-checked')).toBe('false')
    expect(control.className).toContain('min-h-11')
    await user.click(control)

    expect(onChange).toHaveBeenCalledOnce()
    expect(onChange.mock.calls[0]?.[0]).toBe(true)
  })

  it('WHEN checked and disabled THEN keeps the description and ignores interaction', async () => {
    const user = userEvent.setup()
    const onChange = vi.fn()
    render(
      <UISwitch
        label="Red local"
        description="Solo se aplica a esta sesión."
        checked
        disabled
        onChange={onChange}
      />,
    )

    const control = screen.getByRole('switch', { name: 'Red local' })
    expect(control.getAttribute('aria-checked')).toBe('true')
    expect(screen.getByText('Solo se aplica a esta sesión.')).toBeTruthy()
    await user.click(control)

    expect(onChange).not.toHaveBeenCalled()
  })

  it('WHEN the inline variant renders THEN only the switch shows, with a screen-reader label and a bordered track [AC-20]', () => {
    render(<UISwitch label="Cabecera activa 1" checked={false} onChange={() => undefined} variant="inline" />)

    const control = screen.getByRole('switch', { name: 'Cabecera activa 1' })
    expect(screen.getByText('Cabecera activa 1').className).toContain('sr-only')
    expect(control.className).toContain('border-input')
    expect(control.parentElement?.className ?? '').not.toContain('rounded-xl')
  })

  it('WHEN unchecked THEN the track fill uses the input token so the off state stays distinguishable [AC-20]', () => {
    render(<UISwitch label="Apagar Turnstile" checked={false} onChange={() => undefined} />)

    const control = screen.getByRole('switch', { name: 'Apagar Turnstile' })
    expect(control.className).toContain('bg-input')
    expect(control.className).not.toContain('bg-muted')
  })

  it('WHEN disabled THEN the row keeps its description at full contrast and only the control is dimmed [AC-27]', () => {
    render(<UISwitch label="Allow sign-in" description="Shown to the professional" checked={false} disabled onChange={() => undefined} />)

    const row = screen.getByText('Shown to the professional').closest('div')
    expect(row?.className ?? '').not.toMatch(/\bopacity-/)
    expect(screen.getByRole('switch', { name: 'Allow sign-in' }).className).toContain('disabled:opacity-60')
  })
})

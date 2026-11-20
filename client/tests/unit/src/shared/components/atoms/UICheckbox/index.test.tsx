import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { UICheckbox } from '@/shared/components/atoms/UICheckbox'

describe('UICheckbox', () => {
  it('checkbox named by its label that notifies the change', async () => {
    const onChange = vi.fn()
    render(<UICheckbox label="Email notifications" checked={false} onChange={onChange} />)
    await userEvent.setup().click(screen.getByRole('checkbox', { name: 'Email notifications' }))
    expect(onChange).toHaveBeenCalledWith(true)
  })

  it('when disabled describes the reason', () => {
    render(
      <UICheckbox
        label="Email notifications"
        description="Email address unavailable"
        checked={false}
        onChange={vi.fn()}
        disabled
      />,
    )
    const checkbox = screen.getByRole('checkbox', { name: 'Email notifications' })
    expect((checkbox as HTMLInputElement).disabled).toBe(true)
    expect(checkbox.getAttribute('aria-describedby')).toBeTruthy()
    expect(screen.getByText('Email address unavailable')).toBeTruthy()
  })

  it('WHEN the checkbox is enabled THEN its card has the ui-press class [AC-4]', () => {
    render(<UICheckbox label="Email notifications" checked={false} onChange={vi.fn()} />)

    const card = screen.getByRole('checkbox', { name: 'Email notifications' }).closest('label')
    expect(card?.classList.contains('ui-press')).toBe(true)
  })

  it('WHEN it has an error THEN the checkbox is invalid and described by the error', () => {
    render(<UICheckbox label="Consent" description="Required" checked={false} onChange={vi.fn()} error="Confirm the consent" />)

    const checkbox = screen.getByRole('checkbox', { name: 'Consent' })
    expect(checkbox.getAttribute('aria-invalid')).toBe('true')
    const ids = (checkbox.getAttribute('aria-describedby') ?? '').split(' ')
    expect(ids.map((id) => document.getElementById(id)?.textContent)).toEqual(['Required', 'Confirm the consent'])
  })

  it('WHEN it has no error THEN the checkbox is not marked invalid', () => {
    render(<UICheckbox label="Consent" checked={false} onChange={vi.fn()} />)

    expect(screen.getByRole('checkbox', { name: 'Consent' }).getAttribute('aria-invalid')).toBeNull()
  })

  it('WHEN the checkbox is disabled THEN its card has no ui-press class [AC-4]', () => {
    render(<UICheckbox label="Email notifications" checked={false} onChange={vi.fn()} disabled />)

    const card = screen.getByRole('checkbox', { name: 'Email notifications' }).closest('label')
    expect(card?.classList.contains('ui-press')).toBe(false)
  })

  it('WHEN unchecked THEN the native box draws its own input-token border instead of the browser default [R-61]', () => {
    render(<UICheckbox label="Email notifications" checked={false} onChange={vi.fn()} />)

    const box = screen.getByRole('checkbox', { name: 'Email notifications' })
    expect(box.classList.contains('appearance-none')).toBe(true)
    expect(box.classList.contains('border-input')).toBe(true)
    expect(box.classList.contains('bg-background')).toBe(true)
  })

  it('WHEN indeterminate THEN the native box reports the mixed state [AC-3]', () => {
    render(<UICheckbox label="Pacientes" checked={false} indeterminate onChange={vi.fn()} />)

    expect((screen.getByRole('checkbox', { name: 'Pacientes' }) as HTMLInputElement).indeterminate).toBe(true)
  })
})

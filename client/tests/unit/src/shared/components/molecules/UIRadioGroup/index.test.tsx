import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { UIRadioGroup } from '@/shared/components/molecules/UIRadioGroup'

const OPTIONS = [
  { value: 'inbound', label: 'Entrada', description: 'Suma' },
  { value: 'outbound', label: 'Salida' },
]

const SINGLE_OPTION = [{ value: 'adjustment', label: 'Ajuste de inventario' }]

describe('UIRadioGroup [AC-5]', () => {
  it('WHEN an option is chosen THEN notifies the value; group named by its label', async () => {
    const user = userEvent.setup()
    const onChange = vi.fn()
    render(<UIRadioGroup label="Tipo" name="type" options={OPTIONS} value="inbound" onChange={onChange} />)

    expect(screen.getByRole('radiogroup', { name: 'Tipo' })).toBeTruthy()
    await user.click(screen.getByText('Salida'))

    expect(onChange).toHaveBeenCalledWith('outbound')
  })

  it('WHEN the option has a description THEN associates it with the radio', () => {
    render(<UIRadioGroup label="Tipo" name="type" options={OPTIONS} value="inbound" onChange={vi.fn()} />)

    const radio = screen.getByRole('radio', { name: 'Entrada' })
    expect(radio.getAttribute('aria-checked')).toBe('true')
    expect(document.getElementById(radio.getAttribute('aria-describedby') ?? '')?.textContent).toBe('Suma')
    expect(screen.getByRole('radio', { name: 'Salida' }).getAttribute('aria-describedby')).toBeNull()
  })

  it('AC-5: WHEN it gets 1 option THEN shows UIFixedValue, hidden with name and calls onChange if it differs', () => {
    const onChange = vi.fn()
    const { container, rerender } = render(<UIRadioGroup label="Tipo" name="type" options={SINGLE_OPTION} value="" onChange={onChange} />)

    expect(screen.queryByRole('radiogroup')).toBeNull()
    expect(screen.getByRole('term').textContent).toBe('Tipo')
    expect(screen.getByRole('definition').textContent).toBe('Ajuste de inventario')

    const hidden = container.querySelector('input[type="hidden"]') as HTMLInputElement | null
    expect(hidden?.name).toBe('type')
    expect(hidden?.value).toBe('adjustment')

    expect(onChange).toHaveBeenCalledTimes(1)
    expect(onChange).toHaveBeenCalledWith('adjustment')

    rerender(<UIRadioGroup label="Tipo" name="type" options={SINGLE_OPTION} value="adjustment" onChange={onChange} />)
    expect(onChange).toHaveBeenCalledTimes(1)
  })

  it('WHEN a radio option is rendered THEN its card has the ui-press class [AC-4]', () => {
    render(<UIRadioGroup label="Tipo" name="type" options={OPTIONS} value="inbound" onChange={vi.fn()} />)

    const card = screen.getByRole('radio', { name: 'Salida' }).closest('label')
    expect(card?.classList.contains('ui-press')).toBe(true)
  })

  it('WHEN the group is narrow THEN options stack in one column and spread with the container width [AC-1.10]', () => {
    render(<UIRadioGroup label="Tipo" name="type" value="a" onChange={() => {}} options={[{ value: 'a', label: 'A' }, { value: 'b', label: 'B' }]} />)

    const group = screen.getByRole('radiogroup', { name: 'Tipo' })
    expect(group.className).toContain('grid-cols-1')
    expect(group.className).toContain('@xs/radio:grid-cols-2')
    expect(group.className).toContain('@2xl/radio:grid-cols-4')
  })
})

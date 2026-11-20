import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { UICheckboxGroup } from '@/shared/components/molecules/UICheckboxGroup'

const OPTIONS = [
  { value: 'optometry', label: 'Optometría' },
  { value: 'pediatrics', label: 'Pediatría' },
  { value: 'dermatology', label: 'Dermatología' },
]

describe('UICheckboxGroup [AC-7]', () => {
  it('WHEN it has 2+ options THEN opens the menu, allows checking options and calls onChange', async () => {
    const user = userEvent.setup()
    const onChange = vi.fn()
    const { container } = render(
      <UICheckboxGroup
        label="Especialidades"
        name="specialties"
        options={OPTIONS}
        value={['optometry']}
        onChange={onChange}
        summary={(n) => `${n} seleccionadas`}
        placeholder="Selecciona especialidades"
      />,
    )

    // Trigger button is named by its label and contains the summary text
    const trigger = screen.getByRole('button', { name: 'Especialidades' })
    expect(trigger.textContent).toContain('1 seleccionadas')

    // Hidden inputs exist for selected values
    const hiddenInputs = container.querySelectorAll('input[type="hidden"]')
    expect(hiddenInputs.length).toBe(1)
    expect((hiddenInputs[0] as HTMLInputElement).value).toBe('optometry')

    // Click trigger to open dropdown
    await user.click(trigger)

    // Find checkbox items
    const pediatricsItem = await screen.findByRole('menuitemcheckbox', { name: 'Pediatría' })
    expect(pediatricsItem.getAttribute('aria-checked')).toBe('false')

    await user.click(pediatricsItem)
    expect(onChange).toHaveBeenCalledWith(['optometry', 'pediatrics'])
  })

  it('WHEN value is empty THEN the trigger shows the placeholder', () => {
    render(
      <UICheckboxGroup
        label="Especialidades"
        options={OPTIONS}
        value={[]}
        onChange={vi.fn()}
        summary={(n) => `${n} seleccionadas`}
        placeholder="Selecciona especialidades"
      />,
    )

    const trigger = screen.getByRole('button', { name: 'Especialidades' })
    expect(trigger.textContent).toContain('Selecciona especialidades')
  })

  it('WHEN an option is unchecked THEN onChange without that value', async () => {
    const user = userEvent.setup()
    const onChange = vi.fn()
    render(
      <UICheckboxGroup
        label="Especialidades"
        options={OPTIONS}
        value={['optometry', 'pediatrics']}
        onChange={onChange}
        summary={(n) => `${n} seleccionadas`}
        placeholder="Selecciona especialidades"
      />,
    )

    const trigger = screen.getByRole('button', { name: 'Especialidades' })
    expect(trigger.textContent).toContain('2 seleccionadas')

    await user.click(trigger)
    const optometryItem = await screen.findByRole('menuitemcheckbox', { name: 'Optometría' })
    expect(optometryItem.getAttribute('aria-checked')).toBe('true')

    await user.click(optometryItem)
    expect(onChange).toHaveBeenCalledWith(['pediatrics'])
  })

  it('WHEN there is an error THEN aria-invalid on the trigger and visible message', () => {
    render(
      <UICheckboxGroup
        label="Especialidades"
        options={OPTIONS}
        value={[]}
        onChange={vi.fn()}
        summary={(n) => `${n} seleccionadas`}
        placeholder="Selecciona especialidades"
        error="Elige al menos una"
      />,
    )

    const trigger = screen.getByRole('button', { name: 'Especialidades' })
    expect(trigger.getAttribute('aria-invalid')).toBe('true')
    expect(screen.getByText('Elige al menos una')).toBeDefined()
  })

  it('AC-7: WHEN it gets 1 option THEN shows UIFixedValue, hidden with name and auto-selects', () => {
    const onChange = vi.fn()
    const { container, rerender } = render(
      <UICheckboxGroup
        label="Especialidades"
        name="specialties"
        options={[{ value: 'optometry', label: 'Optometría' }]}
        value={[]}
        onChange={onChange}
        summary={(n) => `${n} seleccionadas`}
        placeholder="Selecciona especialidades"
      />,
    )

    expect(screen.queryByRole('button')).toBeNull()
    expect(screen.getByRole('term').textContent).toBe('Especialidades')
    expect(screen.getByRole('definition').textContent).toBe('Optometría')

    const hidden = container.querySelector('input[type="hidden"]') as HTMLInputElement | null
    expect(hidden?.name).toBe('specialties')
    expect(hidden?.value).toBe('optometry')

    expect(onChange).toHaveBeenCalledTimes(1)
    expect(onChange).toHaveBeenCalledWith(['optometry'])

    rerender(
      <UICheckboxGroup
        label="Especialidades"
        name="specialties"
        options={[{ value: 'optometry', label: 'Optometría' }]}
        value={['optometry']}
        onChange={onChange}
        summary={(n) => `${n} seleccionadas`}
        placeholder="Selecciona especialidades"
      />,
    )
    expect(onChange).toHaveBeenCalledTimes(1)
  })
})

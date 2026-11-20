import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { UISearchSelect } from '@/shared/components/molecules/UISearchSelect'

const OPTIONS = [
  { value: 'ana', label: 'Recepción · Ana Pérez', description: 'Registra pacientes' },
  { value: 'luis', label: 'Optometría · Luis Rojas', description: 'Graduación OD/OI' },
  { value: 'elena', label: 'Medicina general · Elena Vásconez' },
]

const skeleton = (container: HTMLElement): Element | null => container.querySelector('[data-slot="skeleton"]')

describe('UISearchSelect', () => {
  // Va primero: es la única prueba del archivo en la que el combobox aún no se descargó.
  it('WHEN there are several options THEN reserves the space while the combobox loads and then shows the chosen option', async () => {
    const { container } = render(<UISearchSelect label="Usuario" empty="Sin coincidencias" options={OPTIONS} value="ana" onChange={vi.fn()} />)

    expect(skeleton(container)).not.toBeNull()
    expect(screen.queryByRole('combobox')).toBeNull()
    const input = (await screen.findByRole('combobox', { name: 'Usuario' })) as HTMLInputElement

    expect(input.value).toBe('Recepción · Ana Pérez')
    expect(skeleton(container)).toBeNull()
  })

  it('WHEN choosing an option THEN notifies its value', async () => {
    const onChange = vi.fn()
    render(<UISearchSelect label="Usuario" empty="Sin coincidencias" options={OPTIONS} value="ana" onChange={onChange} />)

    await userEvent.click(await screen.findByRole('combobox', { name: 'Usuario' }))
    await userEvent.click(await screen.findByRole('option', { name: new RegExp('Optometría · Luis Rojas') }))

    expect(onChange).toHaveBeenCalledWith('luis')
  })

  it('WHEN there is a single option THEN shows a fixed value, notifies it once and does not load the combobox', () => {
    const onChange = vi.fn()
    const { container } = render(
      <UISearchSelect label="Usuario" empty="Sin coincidencias" options={[OPTIONS[1]!]} value="" onChange={onChange} />,
    )

    expect(screen.queryByRole('combobox')).toBeNull()
    expect(skeleton(container)).toBeNull()
    expect(screen.getByText('Optometría · Luis Rojas')).toBeTruthy()
    expect(onChange).toHaveBeenCalledTimes(1)
    expect(onChange).toHaveBeenCalledWith('luis')
  })
})

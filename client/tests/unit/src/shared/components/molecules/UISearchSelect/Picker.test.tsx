/**
 * Pruebas del combobox interno de `UISearchSelect`.
 *
 * @author Pablo Contreras
 * @since 2026/10/08
 */

import { act, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { useState } from 'react'
import { describe, expect, it, vi } from 'vitest'

import { SearchSelectPicker } from '@/shared/components/molecules/UISearchSelect/Picker'

const OPTIONS = [
  { value: 'ana', label: 'Recepción · Ana Pérez', description: 'Registra pacientes' },
  { value: 'luis', label: 'Optometría · Luis Rojas', description: 'Graduación OD/OI' },
  { value: 'elena', label: 'Medicina general · Elena Vásconez' },
]

function Demo({ onChange = vi.fn(), error }: { onChange?: (v: string) => void; error?: string }): React.JSX.Element {
  const [value, setValue] = useState(OPTIONS[0]?.value ?? '')
  return (
    <SearchSelectPicker
      label="Usuario"
      placeholder="Buscar usuario"
      empty="Sin coincidencias"
      options={OPTIONS}
      value={value}
      error={error}
      onChange={(v) => {
        setValue(v)
        onChange(v)
      }}
    />
  )
}

describe('SearchSelectPicker', () => {
  it('WHEN mounted THEN the field shows the chosen option', () => {
    render(<Demo />)

    expect((screen.getByRole('combobox', { name: 'Usuario' }) as HTMLInputElement).value).toBe('Recepción · Ana Pérez')
  })

  it('WHEN typing THEN filters the options and on choosing notifies its value and shows it', async () => {
    const onChange = vi.fn()
    render(<Demo onChange={onChange} />)

    const input = screen.getByRole('combobox', { name: 'Usuario' })
    await userEvent.clear(input)
    await userEvent.type(input, 'opto')
    expect(await screen.findByRole('option', { name: new RegExp('Optometría · Luis Rojas') })).toBeTruthy()
    expect(screen.queryByRole('option', { name: /Elena/ })).toBeNull()
    await userEvent.click(screen.getByRole('option', { name: new RegExp('Optometría · Luis Rojas') }))

    expect(onChange).toHaveBeenCalledWith('luis')
    expect((input as HTMLInputElement).value).toBe('Optometría · Luis Rojas')
  })

  it('WHEN opened with a click THEN lists all options with their description', async () => {
    render(<Demo />)

    await userEvent.click(screen.getByRole('combobox', { name: 'Usuario' }))

    expect(await screen.findAllByRole('option')).toHaveLength(3)
    expect(screen.getByText('Graduación OD/OI')).toBeTruthy()
  })

  it('WHEN there are no matches THEN shows the empty text', async () => {
    render(<Demo />)

    const input = screen.getByRole('combobox', { name: 'Usuario' })
    await userEvent.clear(input)
    await userEvent.type(input, 'zzz')

    expect(await screen.findByText('Sin coincidencias')).toBeTruthy()
  })

  it('WHEN there is an error THEN announces it next to the field', () => {
    render(<Demo error="Elige un usuario" />)

    const input = screen.getByRole('combobox', { name: 'Usuario' })
    expect(input.getAttribute('aria-invalid')).toBe('true')
    expect(screen.getByText('Elige un usuario')).toBeTruthy()
  })

  it('WHEN filterable is false THEN the input is read-only [AC-15]', () => {
    render(
      <SearchSelectPicker
        label="Usuario"
        placeholder="Buscar usuario"
        empty="Sin coincidencias"
        options={OPTIONS}
        value={OPTIONS[0]?.value ?? ''}
        onChange={vi.fn()}
        filterable={false}
      />,
    )

    const input = screen.getByRole('combobox', { name: 'Usuario' })
    expect(input.hasAttribute('readonly')).toBe(true)
  })

  it('WHEN the visible label belongs to the parent field THEN the combobox keeps its explicit accessible name', () => {
    render(
      <SearchSelectPicker
        label="Tipo de identificación"
        empty="Sin coincidencias"
        options={OPTIONS}
        value={OPTIONS[0]?.value ?? ''}
        onChange={vi.fn()}
        showLabel={false}
      />,
    )

    const input = screen.getByRole('combobox', { name: 'Tipo de identificación' })
    expect(input.getAttribute('aria-label')).toBe('Tipo de identificación')
  })

  it('WHEN the input text is cleared THEN onInputCleared is called [AC-17]', async () => {
    const onInputCleared = vi.fn()
    render(
      <SearchSelectPicker
        label="Usuario"
        placeholder="Buscar usuario"
        empty="Sin coincidencias"
        options={OPTIONS}
        value={OPTIONS[0]?.value ?? ''}
        onChange={vi.fn()}
        onInputCleared={onInputCleared}
      />,
    )

    const input = screen.getByRole('combobox', { name: 'Usuario' })
    await userEvent.clear(input)

    expect(onInputCleared).toHaveBeenCalled()
  })

  it('WHEN the input text is cleared and the field loses focus THEN the chosen label returns [AC-17]', async () => {
    const onChange = vi.fn()
    render(
      <SearchSelectPicker
        label="Usuario"
        placeholder="Buscar usuario"
        empty="Sin coincidencias"
        options={OPTIONS}
        value="luis"
        onChange={onChange}
        onInputCleared={vi.fn()}
      />,
    )

    const input = screen.getByRole('combobox', { name: 'Usuario' }) as HTMLInputElement
    await userEvent.clear(input)
    expect(input.value).toBe('')
    expect(onChange).not.toHaveBeenCalled()

    act(() => input.blur())
    expect(input.value).toBe('Optometría · Luis Rojas')
  })

  it('WHEN the user types and then closes the popup with Escape THEN the chosen label returns [AC-17]', async () => {
    render(
      <SearchSelectPicker
        label="Usuario"
        placeholder="Buscar usuario"
        empty="Sin coincidencias"
        options={OPTIONS}
        value="luis"
        onChange={vi.fn()}
      />,
    )

    const input = screen.getByRole('combobox', { name: 'Usuario' }) as HTMLInputElement
    await userEvent.clear(input)
    await userEvent.type(input, 'zzz')
    expect(input.value).toBe('zzz')

    await userEvent.keyboard('{Escape}')
    expect(input.value).toBe('Optometría · Luis Rojas')
  })
})

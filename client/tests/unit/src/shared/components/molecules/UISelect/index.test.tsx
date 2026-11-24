/**
 * Pruebas unitarias de UISelect.
 *
 * @author Pablo Contreras
 * @since 2026/09/27
 */

import { act, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { UISelect } from '@/shared/components/molecules/UISelect'

const TWO_OPTIONS = [
  { value: 'opt1', label: 'Opción 1' },
  { value: 'opt2', label: 'Opción 2' },
]

const NINE_OPTIONS = [
  { value: 'opt1', label: 'Opción 1' },
  { value: 'opt2', label: 'Opción 2' },
  { value: 'opt3', label: 'Opción 3' },
  { value: 'opt4', label: 'Opción 4' },
  { value: 'opt5', label: 'Opción 5' },
  { value: 'opt6', label: 'Opción 6' },
  { value: 'opt7', label: 'Opción 7' },
  { value: 'opt8', label: 'Opción 8' },
  { value: 'opt9', label: 'Opción 9' },
]

const SINGLE_OPTION = [{ value: 'single', label: 'Opción Única' }]

describe('UISelect [AC-15, AC-16, AC-17, AC-18, AC-19, AC-24]', () => {
  // Va primero: es la única prueba donde el combobox aún no se descargó de forma diferida.
  it('WHEN the picker is still loading THEN a 48px skeleton shows [AC-19]', () => {
    const { container } = render(<UISelect label="Cargando" options={TWO_OPTIONS} />)
    const skeleton = container.querySelector('[data-slot="skeleton"]')
    expect(skeleton).not.toBeNull()
    expect(skeleton?.classList.contains('h-12')).toBe(true)
  })

  it('WHEN there are 2 to 8 real options THEN the combobox is read-only and opens on click [AC-15]', async () => {
    render(<UISelect label="Opciones" options={TWO_OPTIONS} value="opt1" />)

    const input = await screen.findByRole('combobox', { name: 'Opciones' })
    expect(input.hasAttribute('readonly')).toBe(true)

    await userEvent.click(input)
    expect(await screen.findByRole('option', { name: 'Opción 1' })).toBeTruthy()
    expect(await screen.findByRole('option', { name: 'Opción 2' })).toBeTruthy()
  })

  it('WHEN there are more than 8 THEN the combobox filters by the typed text [AC-15]', async () => {
    render(<UISelect label="Opciones" options={NINE_OPTIONS} />)

    const input = await screen.findByRole('combobox', { name: 'Opciones' })
    expect(input.hasAttribute('readonly')).toBe(false)

    await userEvent.type(input, 'Opción 9')
    expect(await screen.findByRole('option', { name: 'Opción 9' })).toBeTruthy()
    expect(screen.queryByRole('option', { name: 'Opción 1' })).toBeNull()
  })

  it('WHEN the form submits THEN FormData carries the name and the chosen value [AC-16]', async () => {
    let submittedData: FormData | null = null
    render(
      <form
        onSubmit={(e) => {
          e.preventDefault()
          submittedData = new FormData(e.currentTarget)
        }}
      >
        <UISelect label="Opciones" name="test_field" options={TWO_OPTIONS} defaultValue="opt2" />
        <button type="submit">Submit</button>
      </form>,
    )

    await userEvent.click(screen.getByRole('button', { name: 'Submit' }))
    expect((submittedData as FormData | null)?.get('test_field')).toBe('opt2')
  })

  it('WHEN the select is disabled THEN FormData has no value for it [AC-16]', async () => {
    let submittedData: FormData | null = null
    render(
      <form
        onSubmit={(e) => {
          e.preventDefault()
          submittedData = new FormData(e.currentTarget)
        }}
      >
        <UISelect label="Opciones" name="test_field" options={TWO_OPTIONS} defaultValue="opt2" disabled />
        <button type="submit">Submit</button>
      </form>,
    )

    await userEvent.click(screen.getByRole('button', { name: 'Submit' }))
    expect((submittedData as FormData | null)?.get('test_field')).toBeNull()
  })

  it.each<[string, string | undefined]>([
    ['without an emptyOption', undefined],
    ['with an emptyOption', 'Todas'],
  ])('WHEN there are no real options %s THEN the select is disabled and FormData has no value for it [AC-16]', async (_variant, emptyOption) => {
    let submittedData: FormData | null = null
    render(
      <form
        onSubmit={(e) => {
          e.preventDefault()
          submittedData = new FormData(e.currentTarget)
        }}
      >
        <UISelect label="Opciones" name="test_field" emptyOption={emptyOption} options={[]} />
        <button type="submit">Submit</button>
      </form>,
    )

    const input = (await screen.findByRole('combobox', { name: 'Opciones' })) as HTMLInputElement
    expect(input.disabled).toBe(true)

    await userEvent.click(screen.getByRole('button', { name: 'Submit' }))
    expect((submittedData as FormData | null)?.get('test_field')).toBeNull()
  })

  it('WHEN the user picks the empty row THEN onChange receives an empty string and the hidden input sends it [AC-17]', async () => {
    const onChange = vi.fn()
    let submittedData: FormData | null = null
    render(
      <form
        onSubmit={(e) => {
          e.preventDefault()
          submittedData = new FormData(e.currentTarget)
        }}
      >
        <UISelect
          label="Opciones"
          name="test_field"
          emptyOption="Todas"
          options={TWO_OPTIONS}
          defaultValue="opt1"
          onChange={onChange}
        />
        <button type="submit">Submit</button>
      </form>,
    )

    const input = await screen.findByRole('combobox', { name: 'Opciones' })
    await userEvent.click(input)
    const emptyRow = await screen.findByRole('option', { name: 'Todas' })
    await userEvent.click(emptyRow)

    expect(onChange).toHaveBeenCalledWith('')
    await userEvent.click(screen.getByRole('button', { name: 'Submit' }))
    expect((submittedData as FormData | null)?.get('test_field')).toBe('')
  })

  it('WHEN the input text is cleared with an emptyOption and more than 8 real options THEN onChange receives an empty string and the field shows the empty row on blur [AC-17]', async () => {
    const onChange = vi.fn()
    render(
      <UISelect
        label="Opciones"
        emptyOption="Todas"
        options={NINE_OPTIONS}
        defaultValue="opt9"
        onChange={onChange}
      />,
    )

    const input = await screen.findByRole('combobox', { name: 'Opciones' })
    await userEvent.clear(input)

    expect(onChange).toHaveBeenCalledWith('')

    act(() => input.blur())
    expect((input as HTMLInputElement).value).toBe('Todas')
  })

  it('WHEN the input text is cleared without an emptyOption and more than 8 real options THEN onChange is not called and the chosen label returns [AC-17]', async () => {
    const onChange = vi.fn()
    render(
      <UISelect
        label="Opciones"
        options={NINE_OPTIONS}
        defaultValue="opt9"
        onChange={onChange}
      />,
    )

    const input = (await screen.findByRole('combobox', { name: 'Opciones' })) as HTMLInputElement
    expect(input.value).toBe('Opción 9')
    await userEvent.clear(input)

    expect(input.value).toBe('')
    expect(onChange).not.toHaveBeenCalled()

    act(() => input.blur())
    expect(input.value).toBe('Opción 9')
  })

  it("WHEN there is one real option and an emptyOption THEN the combobox lists the empty row and the option, the value stays '' and neither UIFixedValue nor onChange is used [AC-24]", async () => {
    const onChange = vi.fn()
    let submittedData: FormData | null = null
    render(
      <form
        onSubmit={(e) => {
          e.preventDefault()
          submittedData = new FormData(e.currentTarget)
        }}
      >
        <UISelect
          label="Opciones"
          name="test_field"
          emptyOption="Selecciona"
          options={SINGLE_OPTION}
          onChange={onChange}
        />
        <button type="submit">Submit</button>
      </form>,
    )

    expect(screen.queryByRole('term')).toBeNull()
    expect(onChange).not.toHaveBeenCalled()

    const input = await screen.findByRole('combobox', { name: 'Opciones' })
    await userEvent.click(input)
    expect(await screen.findByRole('option', { name: 'Selecciona' })).toBeTruthy()
    expect(await screen.findByRole('option', { name: 'Opción Única' })).toBeTruthy()

    await userEvent.keyboard('{Escape}')
    await userEvent.click(screen.getByRole('button', { name: 'Submit' }))
    expect((submittedData as FormData | null)?.get('test_field')).toBe('')
  })

  it('WHEN there is one real option and no emptyOption THEN UIFixedValue shows it, onChange receives it once and the combobox does not load [AC-24]', () => {
    const onChange = vi.fn()
    const { container } = render(
      <UISelect
        label="Especialidad"
        name="specialty"
        options={SINGLE_OPTION}
        onChange={onChange}
      />,
    )

    expect(screen.queryByRole('combobox')).toBeNull()
    expect(container.querySelector('[data-slot="skeleton"]')).toBeNull()
    expect(screen.getByRole('term').textContent).toBe('Especialidad')
    expect(screen.getByRole('definition').textContent).toBe('Opción Única')
    expect(onChange).toHaveBeenCalledTimes(1)
    expect(onChange).toHaveBeenCalledWith('single')
  })

  it('WHEN the error is set THEN aria-invalid and aria-describedby point to it [AC-18]', async () => {
    render(<UISelect label="Opciones" options={TWO_OPTIONS} error="Campo obligatorio" />)

    const input = await screen.findByRole('combobox', { name: 'Opciones' })
    expect(input.getAttribute('aria-invalid')).toBe('true')
    const errorId = input.getAttribute('aria-describedby')
    expect(document.getElementById(errorId ?? '')?.textContent).toContain('Campo obligatorio')
  })

  it('WHEN the arrow keys and Enter choose an option THEN onChange is called [AC-18]', async () => {
    const onChange = vi.fn()
    render(<UISelect label="Opciones" options={TWO_OPTIONS} onChange={onChange} />)

    const input = await screen.findByRole('combobox', { name: 'Opciones' })
    await userEvent.click(input)
    await userEvent.keyboard('{ArrowDown}{Enter}')

    expect(onChange).toHaveBeenCalledWith('opt1')
  })

  it('WHEN hideLabel is set THEN the label is screen-reader only and the combobox keeps its name [R-20]', async () => {
    render(<UISelect label="Opciones" options={TWO_OPTIONS} hideLabel />)

    expect(await screen.findByRole('combobox', { name: 'Opciones' })).toBeTruthy()
    expect(screen.getByText('Opciones').classList.contains('sr-only')).toBe(true)
  })

  it('WHEN hideLabel is set on a single option THEN the fixed value term is screen-reader only [R-20]', () => {
    render(<UISelect label="Especialidad" options={SINGLE_OPTION} hideLabel />)

    expect(screen.getByRole('term').classList.contains('sr-only')).toBe(true)
  })
})

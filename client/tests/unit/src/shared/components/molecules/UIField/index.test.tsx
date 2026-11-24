import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { UIField } from '@/shared/components/molecules/UIField'

const describedTexts = (input: HTMLElement): string[] =>
  (input.getAttribute('aria-describedby') ?? '').split(' ').map((id) => document.getElementById(id)?.textContent ?? '')

describe('UIField', () => {
  it('associates the label with the input', () => {
    render(<UIField label="Usuario" name="username" />)

    expect(screen.getByLabelText('Usuario').getAttribute('name')).toBe('username')
    expect(screen.getByLabelText('Usuario').getAttribute('data-slot')).toBe('input')
    expect(screen.getByText('Usuario').getAttribute('data-slot')).toBe('field-label')
  })

  it('WHEN there is an error THEN announces it and marks the input as invalid', () => {
    render(<UIField label="Usuario" name="username" error="Requerido" />)

    const input = screen.getByLabelText('Usuario')
    expect(input.getAttribute('aria-invalid')).toBe('true')
    expect(describedTexts(input)).toEqual(['Requerido'])
  })

  it('WHEN there is no error THEN no invalid mark and no description', () => {
    render(<UIField label="Clave" name="password" type="password" />)

    const input = screen.getByLabelText('Clave')
    expect(input.getAttribute('aria-invalid')).toBeNull()
    expect(input.getAttribute('aria-describedby')).toBeNull()
  })

  it('WHEN icon, end slot and help THEN leaves room on both sides and describes error and help', () => {
    render(<UIField label="Usuario" name="username" icon="user" endSlot={<span>fin</span>} hint="Ayuda" error="Requerido" />)

    const input = screen.getByLabelText('Usuario')
    expect(input.className).toContain('pl-11')
    expect(input.className).toContain('pr-12')
    expect(screen.getByText('fin')).toBeTruthy()
    expect(describedTexts(input)).toEqual(['Requerido', 'Ayuda'])
  })

  it('WHEN hideLabel is set THEN the label is screen-reader only and the input keeps its accessible name [AC-16]', () => {
    render(<UIField label="Nombre de cabecera 1" name="key" hideLabel />)

    expect(screen.getByText('Nombre de cabecera 1').className).toContain('sr-only')
    const input = screen.getByLabelText('Nombre de cabecera 1')
    expect(input.className).toContain('min-h-11')
    expect(input.className).not.toContain('min-h-12')
  })

  it('WHEN a numeric field has a unit THEN the unit sits beside the value and describes the input', () => {
    render(<UIField label="Heart rate" name="hr" type="number" min={20} max={250} unit="lpm" />)

    const input = screen.getByLabelText('Heart rate')
    expect(input.className).toContain('pr-16')
    expect(input.className).toContain('[&::-webkit-inner-spin-button]:appearance-none')
    expect(describedTexts(input)).toEqual(['lpm'])
  })

  it('WHEN a numeric field with range has an error THEN the error states the range with its unit', () => {
    render(<UIField label="Heart rate" name="hr" type="number" min={20} max={250} unit="lpm" error="Out of range" />)

    const input = screen.getByLabelText('Heart rate')
    expect(describedTexts(input)).toEqual(['Out of range', '20–250 lpm', 'lpm'])
  })

  it('WHEN a numeric field with range has no unit THEN the error states the bare range', () => {
    render(<UIField label="Umbral" name="t" type="number" min={-10} max={120} error="Out of range" />)

    expect(describedTexts(screen.getByLabelText('Umbral'))).toEqual(['Out of range', '-10–120'])
  })

  it('WHEN the error already names the range THEN it is not repeated', () => {
    render(<UIField label="Umbral" name="t" type="number" min={-10} max={120} error="Threshold between −10 and 120 dB" />)

    expect(describedTexts(screen.getByLabelText('Umbral'))).toEqual(['Threshold between −10 and 120 dB'])
  })
})

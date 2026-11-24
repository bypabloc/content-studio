import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { UITextarea } from '@/shared/components/molecules/UITextarea'

const described = (el: HTMLElement): string[] =>
  (el.getAttribute('aria-describedby') ?? '').split(' ').map((id) => document.getElementById(id)?.textContent ?? '')

describe('UITextarea', () => {
  it('WHEN rendered THEN visible associated label and no invalid state', () => {
    render(<UITextarea label="Motivo" name="reason" defaultValue="control" />)

    const area = screen.getByLabelText<HTMLTextAreaElement>('Motivo')
    expect(area.tagName).toBe('TEXTAREA')
    expect(area.name).toBe('reason')
    expect(area.value).toBe('control')
    expect(area.getAttribute('aria-invalid')).toBeNull()
    expect(area.getAttribute('aria-describedby')).toBeNull()
  })

  it('WHEN there are error and help THEN marks invalid and describes them', () => {
    render(<UITextarea label="Observaciones" id="obs" error="Obligatorio" hint="Opcional" />)

    const area = screen.getByLabelText('Observaciones')
    expect(area.id).toBe('obs')
    expect(area.getAttribute('aria-invalid')).toBe('true')
    expect(described(area)).toEqual(['Obligatorio', 'Opcional'])
  })

  it('WHEN hideLabel is set THEN the label is screen-reader only and the textarea keeps its accessible name', () => {
    render(<UITextarea label="Medición" hideLabel />)

    expect(screen.getByText('Medición').className).toContain('sr-only')
    expect(screen.getByLabelText('Medición').tagName).toBe('TEXTAREA')
  })
})

import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { UIFixedValue } from '@/shared/components/atoms/UIFixedValue'

describe('UIFixedValue [AC-1]', () => {
  it('WHEN rendered with label, value and name THEN shows term, definition and hidden input', () => {
    const { container } = render(<UIFixedValue label="Especialidad" value="Pediatría" name="specialty" />)

    expect(screen.getByRole('term').textContent).toBe('Especialidad')
    expect(screen.getByRole('definition').textContent).toBe('Pediatría')

    const hidden = container.querySelector('input[type="hidden"]') as HTMLInputElement | null
    expect(hidden).not.toBeNull()
    expect(hidden?.name).toBe('specialty')
    expect(hidden?.value).toBe('Pediatría')
  })

  it('WHEN hiddenValue differs from value THEN uses hiddenValue in the input', () => {
    const { container } = render(<UIFixedValue label="Laboratorio" value="Lab Central" name="laboratory_id" hiddenValue="123" />)

    const hidden = container.querySelector('input[type="hidden"]') as HTMLInputElement | null
    expect(hidden?.value).toBe('123')
  })

  it('WHEN rendered without name THEN no hidden input', () => {
    const { container } = render(<UIFixedValue label="Especialidad" value="Pediatría" />)

    expect(screen.getByRole('term').textContent).toBe('Especialidad')
    expect(screen.getByRole('definition').textContent).toBe('Pediatría')
    expect(container.querySelector('input[type="hidden"]')).toBeNull()
  })
})

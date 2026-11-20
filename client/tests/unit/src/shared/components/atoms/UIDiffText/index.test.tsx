import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { UIDiffText } from '@/shared/components/atoms/UIDiffText'

describe('UIDiffText', () => {
  it('WHEN a word changed THEN the expected one is struck through and the heard one inserted', () => {
    const { container } = render(<UIDiffText label="Cambio" expected="adiós" said="a dios" />)

    expect(screen.getByText('adiós', { selector: 'del' })).toBeTruthy()
    expect(screen.getByText('a dios', { selector: 'ins' })).toBeTruthy()
    expect(container.textContent).toBe('Cambio adiós a dios')
  })
})

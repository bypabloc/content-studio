import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { UIPasswordField } from '@/shared/components/molecules/UIPasswordField'

const renderField = (): void => {
  render(<UIPasswordField label="Contraseña" name="password" revealLabel="Mostrar contraseña" capsLockLabel="Bloq Mayús activado" />)
}

describe('UIPasswordField', () => {
  it('WHEN show is pressed THEN toggles the input type and aria-pressed', () => {
    renderField()
    const input = screen.getByLabelText('Contraseña')
    const toggle = screen.getByRole('button', { name: 'Mostrar contraseña' })

    expect(input.getAttribute('type')).toBe('password')
    fireEvent.click(toggle)
    expect(input.getAttribute('type')).toBe('text')
    expect(toggle.getAttribute('aria-pressed')).toBe('true')
    expect(toggle.getAttribute('aria-controls')).toBe(input.id)
  })

  it('WHEN Caps Lock is on while typing THEN announces it in a live region and removes it when turned off', () => {
    renderField()
    const input = screen.getByLabelText('Contraseña')
    const status = screen.getByRole('status')

    expect(status.textContent).toBe('')
    fireEvent.keyDown(input, { key: 'A', modifierCapsLock: true })
    expect(status.textContent).toBe('Bloq Mayús activado')

    fireEvent.keyUp(input, { key: 'a', modifierCapsLock: false })
    expect(status.textContent).toBe('')
  })

  it('WHEN the visibility toggles THEN the icon is a new node with the fade class [AC-15]', () => {
    renderField()
    const toggle = screen.getByRole('button', { name: 'Mostrar contraseña' })
    const before = toggle.querySelector('svg')

    fireEvent.click(toggle)

    const after = toggle.querySelector('svg')
    expect(after).not.toBe(before)
    expect(after?.getAttribute('class')).toContain('motion-safe:animate-ui-fade')
  })

  it('WHEN hideLabel is set THEN the label is screen-reader only and the reveal control keeps its name [AC-17]', () => {
    render(
      <UIPasswordField
        label="Valor de cabecera 1"
        name="value"
        revealLabel="Mostrar valor de la cabecera 1"
        capsLockLabel="Bloq Mayús está activado"
        hideLabel
      />,
    )

    expect(screen.getByText('Valor de cabecera 1').className).toContain('sr-only')
    expect(screen.getByLabelText('Valor de cabecera 1').getAttribute('type')).toBe('password')
    expect(screen.getByRole('button', { name: 'Mostrar valor de la cabecera 1' })).toBeTruthy()
  })
})

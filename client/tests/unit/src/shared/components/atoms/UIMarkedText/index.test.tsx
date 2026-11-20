import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { UIMarkedText } from '@/shared/components/atoms/UIMarkedText'

describe('UIMarkedText', () => {
  it('WHEN a segment has a message THEN it is marked, with the message as its title', () => {
    render(<UIMarkedText segments={[{ text: 'Hola' }, { text: ';', message: 'Sin ";"' }]} className="x" />)

    const mark = screen.getByTitle('Sin ";"')
    expect(mark.tagName).toBe('MARK')
    expect(mark.textContent).toBe(';')
  })

  it('WHEN it renders THEN it is hidden from assistive technology', () => {
    const { container } = render(<UIMarkedText segments={[{ text: 'Hola' }]} className="x" />)

    expect((container.firstElementChild as HTMLElement).getAttribute('aria-hidden')).toBe('true')
  })

  it('WHEN trailingSpace is set THEN a space follows the text, so a final line break keeps its height', () => {
    const { container } = render(<UIMarkedText segments={[{ text: 'Hola' }]} className="x" trailingSpace />)

    expect(container.firstElementChild?.textContent).toBe('Hola ')
  })
})

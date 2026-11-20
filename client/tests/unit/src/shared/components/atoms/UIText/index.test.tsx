import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { UIText } from '@/shared/components/atoms/UIText'

describe('UIText', () => {
  it('WHEN title THEN it is an h1 heading', () => {
    render(<UIText variant="title">Hola</UIText>)

    expect(screen.getByRole('heading', { level: 1, name: 'Hola' })).toBeTruthy()
  })

  it('WHEN subtitle h2, heading h3; body, caption, overline and display are paragraphs', () => {
    const { container } = render(
      <>
        <UIText variant="subtitle">S</UIText>
        <UIText variant="heading">H</UIText>
        <UIText>B</UIText>
        <UIText variant="caption">C</UIText>
        <UIText variant="overline">O</UIText>
        <UIText variant="display">D</UIText>
      </>,
    )

    expect([...container.children].map((e) => e.tagName)).toEqual(['H2', 'H3', 'P', 'P', 'P', 'P'])
  })

  it('WHEN it gets an id THEN applies it to the element', () => {
    render(<UIText id="reason">M</UIText>)
    expect(document.getElementById('reason')?.textContent).toBe('M')
  })
})

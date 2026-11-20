import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { UIPage } from '@/shared/components/atoms/UIPage'

describe('UIPage', () => {
  it('is the main container of the screen', () => {
    render(<UIPage>hola</UIPage>)

    expect(screen.getByRole('main').textContent).toBe('hola')
  })

  it('WHEN the page mounts THEN the main has the enter class [AC-16]', () => {
    render(<UIPage>hola</UIPage>)

    expect(screen.getByRole('main').classList.contains('motion-safe:animate-ui-enter')).toBe(true)
  })
})

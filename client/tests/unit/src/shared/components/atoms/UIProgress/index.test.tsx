import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { UIProgress } from '@/shared/components/atoms/UIProgress'

describe('UIProgress', () => {
  it('WHEN a job is running THEN it is a named progressbar with its value out of 1', () => {
    render(<UIProgress value={0.4} label="Progreso 40 %" />)

    const bar = screen.getByRole('progressbar', { name: 'Progreso 40 %' })
    expect(bar.getAttribute('aria-valuenow')).toBe('0.4')
    expect(bar.getAttribute('aria-valuemax')).toBe('1')
  })

  it('WHEN the value is 0.4 THEN the fill is 40 percent wide', () => {
    render(<UIProgress value={0.4} label="Progreso 40 %" />)

    const fill = screen.getByRole('progressbar').firstElementChild as HTMLElement
    expect(fill.style.width).toBe('40%')
  })
})

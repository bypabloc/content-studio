import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { UIAlert } from '@/shared/components/molecules/UIAlert'

describe('UIAlert', () => {
  it('WHEN danger (default) THEN announces the message with role alert', () => {
    render(<UIAlert>Failed</UIAlert>)

    expect(screen.getByRole('alert').textContent).toBe('Failed')
    expect(screen.getByRole('alert').getAttribute('data-slot')).toBe('alert')
  })

  it('WHEN info THEN uses role status (non-intrusive announcement)', () => {
    render(<UIAlert tone="info">Saved</UIAlert>)

    expect(screen.getByRole('status').textContent).toBe('Saved')
  })

  it('WHEN a ref, tabIndex and className are given THEN they reach the alert element itself [AC-6]', () => {
    const ref = { current: null as HTMLDivElement | null }
    render(
      <UIAlert ref={ref} tabIndex={-1} className="focus-visible:ui-focus">
        Failed
      </UIAlert>,
    )

    expect(ref.current).toBe(screen.getByRole('alert'))
    expect(screen.getByRole('alert').getAttribute('tabindex')).toBe('-1')
    expect(screen.getByRole('alert').className).toContain('focus-visible:ui-focus')
  })
})

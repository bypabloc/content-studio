import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { UIStatusBadge } from '@/shared/components/atoms/UIStatusBadge'

describe('UIStatusBadge', () => {
  it.each(['pending', 'sent', 'received', 'delivered', 'voided'] as const)('WHEN status %s THEN visible text and decorative icon', (status) => {
    render(<UIStatusBadge status={status} label="Estado" />)

    const badge = screen.getByText('Estado')
    expect(badge.getAttribute('data-status')).toBe(status)
    expect(badge.querySelector('svg')?.getAttribute('aria-hidden')).toBe('true')
  })

  it('WHEN the status changes THEN the badge has the 200 ms color transition [AC-14]', () => {
    const { rerender } = render(<UIStatusBadge status="pending" label="Estado" />)
    const before = screen.getByText('Estado')

    rerender(<UIStatusBadge status="delivered" label="Estado" />)

    const badge = screen.getByText('Estado')
    expect(badge).toBe(before)
    expect(badge.getAttribute('data-status')).toBe('delivered')
    expect(badge.className).toContain('transition-colors')
    expect(badge.className).toContain('duration-200')
    expect(badge.className).toContain('motion-reduce:transition-none')
    expect(badge.className).not.toContain('transition-all')
  })
})

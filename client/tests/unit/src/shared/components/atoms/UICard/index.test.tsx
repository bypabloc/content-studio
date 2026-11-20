import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { UICard } from '@/shared/components/atoms/UICard'

describe('UICard', () => {
  it('groups its content in a labeled section', () => {
    render(<UICard aria-label="Session">content</UICard>)

    expect(screen.getByRole('region', { name: 'Session' }).textContent).toBe('content')
    expect(screen.getByRole('region').getAttribute('data-slot')).toBe('card')
  })
})

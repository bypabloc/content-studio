import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { UIEmpty } from '@/shared/components/molecules/UIEmpty'

describe('UIEmpty [AC-9]', () => {
  it('WHEN shown THEN decorative icon, title, description and action', () => {
    const { container } = render(<UIEmpty icon="users" title="No users" description="Create the first one" action={<button type="button">New</button>} />)

    expect(screen.getByRole('heading', { level: 2, name: 'No users' })).toBeTruthy()
    expect(screen.getByText('Create the first one')).toBeTruthy()
    expect(screen.getByRole('button', { name: 'New' })).toBeTruthy()
    expect(container.querySelector('svg')?.getAttribute('aria-hidden')).toBe('true')
  })

  it('WHEN there is no description or action THEN only the title', () => {
    render(<UIEmpty icon="shield-alert" title="No permission" />)

    expect(screen.getByRole('heading', { name: 'No permission' })).toBeTruthy()
  })

  it('WHEN level=4 THEN the title is an h4 (inside a card with h3)', () => {
    render(<UIEmpty icon="chart-column" title="No data" level={4} />)

    expect(screen.getByRole('heading', { level: 4, name: 'No data' })).toBeTruthy()
  })

  it('WHEN level=1 THEN the title is the h1 of a screen without another heading', () => {
    render(<UIEmpty icon="link" title="Invalid link" level={1} />)

    expect(screen.getByRole('heading', { level: 1, name: 'Invalid link' })).toBeTruthy()
  })
})

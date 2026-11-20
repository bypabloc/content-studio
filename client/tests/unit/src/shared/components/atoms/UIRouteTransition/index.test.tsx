import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { UIRouteTransition } from '@/shared/components/atoms/UIRouteTransition'

describe('UIRouteTransition', () => {
  it('WHEN rendered THEN children are wrapped with motion-safe:animate-ui-enter [AC-16]', () => {
    render(
      <UIRouteTransition>
        <p>page content</p>
      </UIRouteTransition>,
    )

    expect(screen.getByText('page content').parentElement?.className).toContain('motion-safe:animate-ui-enter')
  })
})

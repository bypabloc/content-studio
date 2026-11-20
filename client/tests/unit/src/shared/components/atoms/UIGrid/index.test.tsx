import { render } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { UIGrid } from '@/shared/components/atoms/UIGrid'

describe('UIGrid', () => {
  it('WHEN 3 columns (default) THEN 1 on mobile, 2 on tablet and 3 on desktop', () => {
    const { container } = render(<UIGrid>x</UIGrid>)

    expect(container.firstElementChild?.className).toContain('sm:grid-cols-2 lg:grid-cols-3')
  })

  it('WHEN 2 columns THEN never more than 2', () => {
    const { container } = render(<UIGrid columns={2}>x</UIGrid>)

    expect(container.firstElementChild?.className).not.toContain('lg:grid-cols-3')
  })

  it('WHEN 4 columns THEN two on tablet and four on wide desktop, so no row keeps a single card [AC-4.4]', () => {
    const { container } = render(<UIGrid columns={4}>x</UIGrid>)

    expect(container.firstElementChild?.className).toContain('sm:grid-cols-2 xl:grid-cols-4')
    expect(container.firstElementChild?.className).not.toContain('lg:grid-cols-3')
  })

  it('WHEN compact THEN three columns on mobile and four from tablet for short chips [AC-2.9]', () => {
    const { container } = render(<UIGrid columns="compact">x</UIGrid>)

    expect(container.firstElementChild?.className).toContain('grid-cols-3 gap-2 sm:grid-cols-4')
    expect(container.firstElementChild?.className).not.toContain('grid-cols-1')
  })
})

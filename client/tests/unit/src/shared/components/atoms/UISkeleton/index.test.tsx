import { render } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { UISkeleton } from '@/shared/components/atoms/UISkeleton'

describe('UISkeleton', () => {
  it('reserves the given space, hidden and without animation under reduced-motion', () => {
    const { container } = render(<UISkeleton className="h-8 w-40" />)

    const block = container.firstElementChild
    expect(block?.getAttribute('aria-hidden')).toBe('true')
    expect(block?.getAttribute('data-slot')).toBe('skeleton')
    expect(block?.className).toContain('h-8 w-40')
    expect(block?.className).toContain('motion-reduce:animate-none')
  })
})

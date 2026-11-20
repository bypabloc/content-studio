import { render } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { UIAvatar } from '@/shared/components/atoms/UIAvatar'

describe('UIAvatar', () => {
  it('WHEN first and last name THEN initials of both, decorative', () => {
    const { container } = render(<UIAvatar name="ana pérez soto" />)

    const avatar = container.firstElementChild
    expect(avatar?.textContent).toBe('AP')
    expect(avatar?.getAttribute('aria-hidden')).toBe('true')
    expect(avatar?.getAttribute('data-slot')).toBe('avatar')
  })

  it('WHEN a single name THEN one initial', () => {
    const { container } = render(<UIAvatar name="  Ana " />)

    expect(container.textContent).toBe('A')
  })
})

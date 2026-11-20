import { render } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { UITime } from '@/shared/components/atoms/UITime'

describe('UITime', () => {
  it('marca la fecha con su valor ISO y muestra el texto legible', () => {
    const { container } = render(<UITime dateTime="2026-09-20T10:00:00Z">20 sept 2026</UITime>)

    const time = container.querySelector('time')
    expect(time?.getAttribute('datetime')).toBe('2026-09-20T10:00:00Z')
    expect(time?.textContent).toBe('20 sept 2026')
  })
})

import { describe, expect, it } from 'vitest'

import { navItems } from '@/app/nav'

describe('navItems (spec 009, AC-3)', () => {
  it('WHEN the sections are listed THEN each one has its icon name from the map of UIIcon', () => {
    expect(navItems().map((item) => [item.id, item.icon])).toEqual([
      ['narration', 'narration'],
      ['settings', 'settings'],
    ])
  })
})

import { describe, expect, expectTypeOf, it } from 'vitest'

import { FLOATING_TOOLBAR_PLACEMENTS, type FloatingToolbarPlacement } from '@/shared/components/organisms/UIFloatingToolbar/types'

describe('tipos de UIFloatingToolbar', () => {
  it('WHEN the placements are listed THEN the toolbar has its eight positions', () => {
    expect(FLOATING_TOOLBAR_PLACEMENTS).toHaveLength(8)
    expect(FLOATING_TOOLBAR_PLACEMENTS).toContain('bottom-right')
  })

  it('WHEN a placement is typed THEN it is one of the listed values', () => {
    expectTypeOf<FloatingToolbarPlacement>().toEqualTypeOf<(typeof FLOATING_TOOLBAR_PLACEMENTS)[number]>()
  })
})

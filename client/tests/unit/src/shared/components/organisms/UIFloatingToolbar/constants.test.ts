import { describe, expect, it } from 'vitest'

import { HIDE_DELAY_MS, PLACEMENT_CLASSES, TOOLTIP_DELAY_MS } from '@/shared/components/organisms/UIFloatingToolbar/constants'
import { FLOATING_TOOLBAR_PLACEMENTS } from '@/shared/components/organisms/UIFloatingToolbar/types'

describe('constantes de UIFloatingToolbar', () => {
  it('WHEN the bar is idle THEN it hides after 2 s and tooltips open after 200 ms', () => {
    expect(HIDE_DELAY_MS).toBe(2000)
    expect(TOOLTIP_DELAY_MS).toBe(200)
  })

  it('WHEN a placement is given THEN it has its position and handle classes', () => {
    for (const placement of FLOATING_TOOLBAR_PLACEMENTS) {
      expect(PLACEMENT_CLASSES[placement].root).toBeTruthy()
      expect(PLACEMENT_CLASSES[placement].handle).toBeTruthy()
    }
  })

  it('WHEN the bar sits on a side THEN it is vertical, and on top or bottom it is horizontal', () => {
    expect(PLACEMENT_CLASSES.left.orientation).toBe('vertical')
    expect(PLACEMENT_CLASSES.right.orientation).toBe('vertical')
    expect(PLACEMENT_CLASSES.top.orientation).toBe('horizontal')
    expect(PLACEMENT_CLASSES['bottom-left'].orientation).toBe('horizontal')
  })
})

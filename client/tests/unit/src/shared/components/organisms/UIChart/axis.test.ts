import { describe, expect, it } from 'vitest'

import { axisWidth } from '@/shared/components/organisms/UIChart/axis'

describe('axisWidth [AC-6.6]', () => {
  it('WHEN amounts are long THEN the Y axis reserves room for the whole label', () => {
    const formatY = (value: number): string => `$${value.toLocaleString('es', { minimumFractionDigits: 2 })}`
    const width = axisWidth({ data: [{ x: 'a', revenue: 12500 }], series: [{ key: 'revenue', label: 'Ingresos' }], formatY })
    expect(width).toBeGreaterThanOrEqual(formatY(12500).length * 7)
  })

  it('WHEN values are short THEN the axis keeps a minimum width', () => {
    expect(axisWidth({ data: [{ x: 'a', n: 3 }], series: [{ key: 'n', label: 'N' }], formatY: String })).toBe(40)
  })
})

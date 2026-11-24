import { describe, expectTypeOf, it } from 'vitest'

import type { ChartBand, ChartKind, ChartSeries, Row } from '@/shared/components/organisms/UIChart/types'

// Módulo solo de tipos: sus pruebas se comprueban en compilación (`expectTypeOf`); en ejecución no hay código que correr.
describe('tipos de UIChart', () => {
  it('WHEN a chart kind is chosen THEN it is one of the eight shapes', () => {
    expectTypeOf<ChartKind>().toEqualTypeOf<'bar' | 'bar-horizontal' | 'bar-stacked' | 'bar-grouped' | 'line' | 'area' | 'donut' | 'curves'>()
  })

  it('WHEN a series takes a palette color THEN only slots 1 to 5 are valid', () => {
    expectTypeOf<ChartSeries['color']>().toEqualTypeOf<1 | 2 | 3 | 4 | 5 | undefined>()
  })

  it('WHEN a band is given THEN both limits are optional and it has a label', () => {
    expectTypeOf<ChartBand>().toEqualTypeOf<{ low?: number; high?: number; label: string }>()
  })

  it('WHEN a row is read THEN each column is text, a number or null', () => {
    expectTypeOf<Row>().toEqualTypeOf<Record<string, string | number | null>>()
  })
})

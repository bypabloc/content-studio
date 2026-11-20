import type { ChartSeries, Row } from './types'

type AxisInput = { data: Row[]; series: ChartSeries[]; formatY: (value: number) => string }

/** Ancho del eje Y según la etiqueta más larga (≈7 px por carácter a 12 px): montos como «$10.000,00» no se cortan. */
export const axisWidth = ({ data, series, formatY }: AxisInput): number => {
  const values = data.flatMap((row) => series.map((s) => Number(row[s.key] ?? 0)))
  const max = Math.max(0, ...values.map((value) => Math.abs(value)))
  return Math.max(40, Math.ceil(formatY(max).length * 7 + 12))
}

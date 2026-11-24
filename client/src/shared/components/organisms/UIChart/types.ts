/** Forma de la gráfica. */
export type ChartKind = 'bar' | 'bar-horizontal' | 'bar-stacked' | 'bar-grouped' | 'line' | 'area' | 'donut' | 'curves'

/**
 * Serie: clave del dato, etiqueta visible y color de la paleta (`--chart-1..5`).
 * En líneas y curvas, `stroke` y `marker` distinguen series sin depender del
 * color y `join` conecta los puntos por encima de los huecos (`connectNulls`).
 */
export type ChartSeries = {
  key: string
  label: string
  color?: 1 | 2 | 3 | 4 | 5
  stroke?: 'solid' | 'dashed' | 'dotted'
  marker?: 'none' | 'circle' | 'cross'
  join?: boolean
}

/** Franja de referencia (D-7): entre `low` y `high`; sin un extremo, llega al borde de los datos. */
export type ChartBand = { low?: number; high?: number; label: string }

export type Row = Record<string, string | number | null>

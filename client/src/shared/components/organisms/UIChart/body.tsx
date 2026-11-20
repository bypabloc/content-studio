import type { ReactElement } from 'react'
import { Area, AreaChart, Bar, BarChart, CartesianGrid, Line, LineChart, Pie, PieChart, ReferenceArea, XAxis, YAxis } from 'recharts'

import { useReducedMotion } from '@/shared/hooks/use-reduced-motion'
import { type ChartConfig, ChartContainer, ChartLegend, ChartLegendContent, ChartTooltip, ChartTooltipContent } from '../../shadcn/chart'
import { UIChartMarker } from '../../atoms/UIChartMarker'
import { UIText } from '../../atoms/UIText'

import { axisWidth } from './axis'
import type { ChartBand, ChartKind, ChartSeries, Row } from './types'

type Props = {
  kind: ChartKind
  data: Row[]
  series: ChartSeries[]
  xKey: string
  formatX?: (value: string) => string
  formatY?: (value: number) => string
  height?: number
  ariaLabel: string
  /** Dominio del eje X numérico (`kind="curves"`). */
  xDomain?: [number, number]
  /** Decimales del eje Y (por defecto 0: conteos). */
  decimalsY?: number
  /** Escala del eje X numérico (`kind="curves"`): `log` da igual distancia por octava. */
  xScale?: 'linear' | 'log'
  /** Ticks fijos del eje X (`kind="curves"`). */
  xTicks?: number[]
  /** Eje Y creciente hacia abajo (`kind="curves"`, p. ej. audiograma). */
  yInverted?: boolean
  /** Dominio fijo del eje Y (`kind="curves"`). */
  yDomain?: [number, number]
  /** Franja de referencia con su etiqueta (`line` y `area`, AC-7). */
  band?: ChartBand
  /** Línea extra del tooltip de cada punto (p. ej., las lecturas originales); sin valor, no agrega nada. */
  tooltipDetail?: (row: Row) => string | undefined
}

type Ctx = Required<Pick<Props, 'data' | 'series' | 'xKey' | 'formatX' | 'formatY' | 'decimalsY'>> & Pick<Props, 'xDomain' | 'xScale' | 'xTicks' | 'yInverted' | 'yDomain' | 'band' | 'tooltipDetail'> & { animate: boolean }

const paletteColor = (slot: number): string => `var(--chart-${slot})`
const seriesColor = (s: ChartSeries, i: number): string => paletteColor(s.color ?? (i % 5) + 1)
const fillOf = (key: string): string => `var(--color-${key})`

const identity = (value: string): string => value
const toLocale = (value: number): string => value.toLocaleString('es')
const withDecimals =
  (decimals: number) =>
  (value: number): string =>
    value.toLocaleString('es', { maximumFractionDigits: decimals })

// Recharts anima con JavaScript y la regla CSS global de reduced motion no la
// cubre: las series animan salvo que el usuario pida reducir el movimiento
// (`animate`, de useReducedMotion); el tooltip nunca anima. Los ejes de
// conteos no muestran decimales.
// Ticks chicos y espaciados: a 375px no se pisan (preserveStartEnd + minTickGap).
const TICK = { fontSize: 12 } as const

const tooltip = ({ formatX, formatY, tooltipDetail }: Ctx): ReactElement => {
  const labelFormatter = (label: unknown): string => formatX(String(label))
  if (!tooltipDetail) return <ChartTooltip isAnimationActive={false} content={<ChartTooltipContent valueFormatter={formatY} labelFormatter={labelFormatter} />} />
  return (
    <ChartTooltip
      isAnimationActive={false}
      content={(props) => {
        const row = props.payload?.[0]?.payload as Row | undefined
        const detail = props.active && row ? tooltipDetail(row) : undefined
        return (
          <>
            <ChartTooltipContent active={props.active} payload={props.payload} label={props.label} valueFormatter={formatY} labelFormatter={labelFormatter} />
            {detail ? <UIText className="px-2.5 pb-1.5 text-xs text-foreground-secondary">{detail}</UIText> : null}
          </>
        )
      }}
    />
  )
}

// La leyenda se parte en varias líneas: a 375px no se sale de la tarjeta.
const legend = ({ series }: Ctx): ReactElement | null => (series.length > 1 ? <ChartLegend content={<ChartLegendContent className="flex-wrap gap-x-4 gap-y-1" />} /> : null)

const categoryAxis = ({ xKey, formatX }: Ctx): ReactElement => (
  <XAxis dataKey={xKey} tickLine={false} axisLine={false} tickMargin={8} tick={TICK} minTickGap={16} interval="preserveStartEnd" tickFormatter={(v) => formatX(String(v))} />
)

const valueAxis = (ctx: Ctx): ReactElement => {
  const { formatY, decimalsY, yInverted = false, yDomain } = ctx
  return (
    <YAxis allowDecimals={decimalsY > 0} reversed={yInverted} domain={yDomain ?? (decimalsY > 0 ? ['auto', 'auto'] : undefined)} tickLine={false} axisLine={false} tickMargin={4} tick={TICK} width={axisWidth(ctx)} tickFormatter={(v: number) => formatY(v)} />
  )
}

/** Franja de referencia: sin un extremo, llega al borde del dominio vertical (`yDomain`) o de los datos (D-7). */
const bandArea = ({ band, data, series, yDomain }: Ctx): ReactElement | null => {
  if (!band) return null
  const values = data.flatMap((row) => series.map((s) => row[s.key])).filter((v): v is number => typeof v === 'number' && Number.isFinite(v))
  if (values.length === 0 && (band.low === undefined || band.high === undefined)) return null
  const y1 = band.low ?? yDomain?.[0] ?? Math.min(...values)
  const y2 = band.high ?? yDomain?.[1] ?? Math.max(...values)
  return (
    <ReferenceArea
      y1={y1}
      y2={y2}
      ifOverflow="extendDomain"
      fill="var(--chart-2)"
      fillOpacity={0.15}
      stroke="none"
      label={{ value: band.label, position: 'insideTopLeft', fill: 'var(--foreground-secondary)', fontSize: 12 }}
    />
  )
}

const DASH = { solid: undefined, dashed: '6 4', dotted: '2 3' } as const

type MarkerProps = { cx?: number; cy?: number; index?: number }

// Cruz como marcador: se distingue del círculo sin depender del color.
const cross =
  (color: string) =>
  ({ cx, cy, index }: MarkerProps): ReactElement => (
    <UIChartMarker key={index} cx={cx} cy={cy} color={color} />
  )

const dotOf = (s: ChartSeries): false | { r: number; fill: string; strokeWidth: number } | ((p: MarkerProps) => ReactElement) => {
  if (s.marker === 'circle') return { r: 4, fill: fillOf(s.key), strokeWidth: 0 }
  if (s.marker === 'cross') return cross(fillOf(s.key))
  return false
}

const lineOf = (s: ChartSeries, type: 'monotone' | 'linear', animate: boolean): ReactElement => (
  <Line
    key={s.key}
    isAnimationActive={animate}
    animationDuration={400}
    animationEasing="ease-out"
    dataKey={s.key}
    name={s.label}
    type={type}
    stroke={fillOf(s.key)}
    strokeWidth={2}
    strokeDasharray={DASH[s.stroke ?? 'solid']}
    dot={dotOf(s)}
    connectNulls={s.join ?? false}
  />
)

const bars = (ctx: Ctx, stackId?: string): ReactElement => (
  <BarChart accessibilityLayer data={ctx.data}>
    <CartesianGrid vertical={false} />
    {categoryAxis(ctx)}
    {valueAxis(ctx)}
    {tooltip(ctx)}
    {legend(ctx)}
    {ctx.series.map((s, i) => (
      <Bar key={s.key} isAnimationActive={ctx.animate} animationDuration={400} animationEasing="ease-out" dataKey={s.key} fill={fillOf(s.key)} stackId={stackId} radius={stackId && i < ctx.series.length - 1 ? 0 : [4, 4, 0, 0]} />
    ))}
  </BarChart>
)

const RENDER: Record<ChartKind, (ctx: Ctx) => ReactElement> = {
  bar: (ctx) => bars(ctx),
  'bar-grouped': (ctx) => bars(ctx),
  'bar-stacked': (ctx) => bars(ctx, 'total'),
  'bar-horizontal': (ctx) => (
    <BarChart accessibilityLayer data={ctx.data} layout="vertical" margin={{ left: 0, right: 8 }}>
      <CartesianGrid horizontal={false} />
      <XAxis type="number" allowDecimals={false} tickLine={false} axisLine={false} tick={TICK} minTickGap={16} interval="preserveStartEnd" tickFormatter={(v: number) => ctx.formatY(v)} />
      <YAxis type="category" dataKey={ctx.xKey} tickLine={false} axisLine={false} tick={TICK} width={132} interval={0} tickFormatter={(v) => ctx.formatX(String(v))} />
      {tooltip(ctx)}
      {legend(ctx)}
      {ctx.series.map((s) => (
        <Bar key={s.key} isAnimationActive={ctx.animate} animationDuration={400} animationEasing="ease-out" dataKey={s.key} fill={fillOf(s.key)} radius={[0, 4, 4, 0]} />
      ))}
    </BarChart>
  ),
  line: (ctx) => (
    <LineChart accessibilityLayer data={ctx.data}>
      <CartesianGrid vertical={false} />
      {categoryAxis(ctx)}
      {valueAxis(ctx)}
      {tooltip(ctx)}
      {legend(ctx)}
      {bandArea(ctx)}
      {ctx.series.map((s) => lineOf(s, 'monotone', ctx.animate))}
    </LineChart>
  ),
  curves: (ctx) => (
    <LineChart accessibilityLayer data={ctx.data}>
      <CartesianGrid />
      <XAxis
        type="number"
        dataKey={ctx.xKey}
        scale={ctx.xScale === 'log' ? 'log' : 'auto'}
        ticks={ctx.xTicks}
        domain={ctx.xDomain ?? (ctx.xTicks ? [ctx.xTicks[0] ?? 0, ctx.xTicks.at(-1) ?? 0] : ['dataMin', 'dataMax'])}
        allowDecimals={false} tickLine={false} axisLine={false} tickMargin={8} tick={TICK} minTickGap={16} tickFormatter={(v) => ctx.formatX(String(v))} />
      {valueAxis(ctx)}
      {tooltip(ctx)}
      {legend(ctx)}
      {ctx.series.map((s) => lineOf(s, 'linear', ctx.animate))}
    </LineChart>
  ),
  area: (ctx) => (
    <AreaChart accessibilityLayer data={ctx.data}>
      <CartesianGrid vertical={false} />
      {categoryAxis(ctx)}
      {valueAxis(ctx)}
      {tooltip(ctx)}
      {legend(ctx)}
      {bandArea(ctx)}
      {ctx.series.map((s) => (
        <Area key={s.key} isAnimationActive={ctx.animate} animationDuration={400} animationEasing="ease-out" dataKey={s.key} type="monotone" stroke={fillOf(s.key)} fill={fillOf(s.key)} fillOpacity={0.2} strokeWidth={2} />
      ))}
    </AreaChart>
  ),
  donut: ({ data, series, xKey, formatY, animate }) => (
    <PieChart accessibilityLayer>
      <ChartTooltip isAnimationActive={false} content={<ChartTooltipContent hideLabel nameKey={xKey} valueFormatter={formatY} />} />
      <ChartLegend content={<ChartLegendContent nameKey={xKey} className="flex-wrap gap-x-4 gap-y-1" />} />
      <Pie isAnimationActive={animate} animationDuration={400} animationEasing="ease-out" data={data.map((row, i) => ({ ...row, fill: paletteColor((i % 5) + 1) }))} dataKey={series[0]?.key ?? ''} nameKey={xKey} innerRadius="55%" strokeWidth={2} />
    </PieChart>
  ),
}

// El donut nombra categorías (filas); el resto, series.
const configOf = ({ kind, data, series, xKey, formatX }: Pick<Props, 'kind' | 'data' | 'series' | 'xKey'> & { formatX: (v: string) => string }): ChartConfig =>
  kind === 'donut'
    ? Object.fromEntries(data.map((row) => [String(row[xKey]), { label: formatX(String(row[xKey])) }]))
    : Object.fromEntries(series.map((s, i) => [s.key, { label: s.label, color: seriesColor(s, i) }]))

/**
 * Gráfica sobre shadcn Charts (Recharts v3) con la paleta `--chart-1..5`:
 * barras (verticales, horizontales, apiladas o agrupadas), líneas, áreas,
 * dona o curvas (líneas sobre un eje X numérico con `xDomain`, p. ej. percentiles
 * por edad, con `stroke`/`marker` por serie y `decimalsY` en el eje Y; `xScale="log"`
 * con `xTicks` y `yInverted` con `yDomain` dibujan un audiograma). Arma el `ChartConfig` desde `series`, formatea ejes y tooltip con
 * `formatX`/`formatY`, muestra leyenda con más de una serie (la dona siempre)
 * y se expone como figura con `ariaLabel`; `accessibilityLayer` permite
 * recorrerla con el teclado. Las series animan (400 ms, `ease-out`) salvo que el
 * usuario pida reducir el movimiento; el tooltip no anima. `band` dibuja una
 * franja de referencia entre `low` y `high` en `line` y `area`.
 *
 * @author Pablo Contreras
 * @since 2026/09/28
 */
export function UIChartBody({ kind, data, series, xKey, formatX = identity, formatY, height = 280, ariaLabel, xDomain, decimalsY = 0, xScale, xTicks, yInverted, yDomain, band, tooltipDetail }: Props): React.JSX.Element {
  const animate = !useReducedMotion()
  return (
    <ChartContainer
      role="figure"
      aria-label={ariaLabel}
      config={configOf({ kind, data, series, xKey, formatX })}
      height={height}
      initialDimension={{ width: 320, height }}
      className="aspect-auto w-full min-w-0"
    >
      {RENDER[kind]({ data, series, xKey, formatX, formatY: formatY ?? (decimalsY > 0 ? withDecimals(decimalsY) : toLocale), xDomain, decimalsY, xScale, xTicks, yInverted, yDomain, band, tooltipDetail, animate })}
    </ChartContainer>
  )
}

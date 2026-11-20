import { render, screen, waitFor } from '@testing-library/react'
import type { ComponentProps } from 'react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { type ChartKind, UIChart } from '@/shared/components/organisms/UIChart'

// Recharts 3 no dibuja las barras en jsdom: se capturan sus props.
const barProps = vi.hoisted((): Record<string, unknown>[] => [])
const captured = vi.hoisted(() => ({
  lines: [] as Record<string, unknown>[],
  areas: [] as Record<string, unknown>[],
  pies: [] as Record<string, unknown>[],
  tooltips: [] as Record<string, unknown>[],
  axesX: [] as Record<string, unknown>[],
  axesY: [] as Record<string, unknown>[],
  refAreas: [] as Record<string, unknown>[],
}))
vi.mock('recharts', async (importOriginal) => {
  const recharts = await importOriginal<typeof import('recharts')>()
  const Bar = (props: ComponentProps<typeof recharts.Bar>): React.JSX.Element => {
    barProps.push({ ...props })
    return <recharts.Bar {...props} />
  }
  const Line = (props: ComponentProps<typeof recharts.Line>): React.JSX.Element => {
    captured.lines.push({ ...props })
    return <recharts.Line {...props} />
  }
  const Area = (props: ComponentProps<typeof recharts.Area>): React.JSX.Element => {
    captured.areas.push({ ...props })
    return <recharts.Area {...props} />
  }
  const Pie = (props: ComponentProps<typeof recharts.Pie>): React.JSX.Element => {
    captured.pies.push({ ...props })
    return <recharts.Pie {...props} />
  }
  const Tooltip = (props: ComponentProps<typeof recharts.Tooltip>): React.JSX.Element => {
    captured.tooltips.push({ ...props })
    return <recharts.Tooltip {...props} />
  }
  const XAxis = (props: ComponentProps<typeof recharts.XAxis>): React.JSX.Element => {
    captured.axesX.push({ ...props })
    return <recharts.XAxis {...props} />
  }
  const YAxis = (props: ComponentProps<typeof recharts.YAxis>): React.JSX.Element => {
    captured.axesY.push({ ...props })
    return <recharts.YAxis {...props} />
  }
  const ReferenceArea = (props: ComponentProps<typeof recharts.ReferenceArea>): React.JSX.Element => {
    captured.refAreas.push({ ...props })
    return <recharts.ReferenceArea {...props} />
  }
  return { ...recharts, Area, Bar, Line, Pie, ReferenceArea, Tooltip, XAxis, YAxis }
})

const DATA = [
  { x: 'pending', orders: 1, others: 2 },
  { x: 'sent', orders: 3, others: 1 },
  { x: 'delivered', orders: 2, others: 0 },
]

const draw = (kind: ChartKind, extra: Partial<Parameters<typeof UIChart>[0]> = {}): ReturnType<typeof render> =>
  render(
    <UIChart
      kind={kind}
      data={DATA}
      xKey="x"
      series={[
        { key: 'orders', label: 'Orders' },
        { key: 'others', label: 'Others', color: 3 },
      ]}
      ariaLabel="Orders by status"
      {...extra}
    />,
  )

// El setup global deja `window.matchMedia` como función simple: se guarda antes de espiarla, para que las llamadas no
// se encadenen sobre el propio espía (lo que desbordaba la pila).
const baseMatchMedia = window.matchMedia

/** Simula la preferencia de movimiento reducido (el setup global responde `matches: false`). */
const preferReducedMotion = (reduced: boolean): void => {
  vi.spyOn(window, 'matchMedia').mockImplementation((query) => ({ ...baseMatchMedia(query), matches: reduced }))
}

/** Vacía las capturas de recharts antes de dibujar. */
const resetCaptured = (): void => {
  barProps.length = 0
  for (const list of Object.values(captured)) list.length = 0
}

/** `UIChart` carga recharts al primer uso (lazy): hasta que dibuja, muestra el esqueleto. */
const ready = (): Promise<HTMLElement[]> => screen.findAllByRole('figure')

// jsdom no mide: ResponsiveContainer necesita un tamaño para dibujar el SVG.
beforeEach(() => {
  vi.spyOn(HTMLElement.prototype, 'getBoundingClientRect').mockReturnValue(new DOMRect(0, 0, 600, 300))
})

afterEach(() => {
  vi.restoreAllMocks()
})

describe('UIChart carga perezosa [AC-9]', () => {
  // Va primero: solo la primera gráfica del archivo muestra el esqueleto; después recharts ya está cargado.
  it('WHEN the chart is still loading THEN the placeholder reserves the final height', async () => {
    const { container } = draw('bar', { height: 300 })

    expect(container.querySelector('[data-slot="chart-placeholder"]')?.getAttribute('height')).toBe('300')
    expect(await screen.findByRole('figure', { name: 'Orders by status' })).toBeTruthy()
  })
})

describe('UIChart [AC-9]', () => {
  it.each<ChartKind>(['bar', 'bar-grouped', 'bar-stacked', 'bar-horizontal', 'line', 'area', 'donut'])('WHEN kind=%s THEN figure with aria-label and SVG', async (kind) => {
    const { container } = draw(kind)

    expect(await screen.findByRole('figure', { name: 'Orders by status' })).toBeTruthy()
    expect(container.querySelector('svg')).toBeTruthy()
  })

  it('WHEN several series THEN config with the palette and legend', async () => {
    const { container } = draw('bar')

    await ready()
    const css = container.querySelector('style')?.innerHTML ?? ''
    expect(css).toContain('--color-orders: var(--chart-1);')
    expect(css).toContain('--color-others: var(--chart-3);')
  })

  it('WHEN kind=donut THEN one sector per category with its palette color', async () => {
    // Sin animación: en jsdom la animación de los sectores tarda más que el waitFor.
    preferReducedMotion(true)
    const { container } = draw('donut', { formatX: (v) => v.toUpperCase() })

    // Recharts 3 dibuja los sectores tras sincronizar su store (asíncrono).
    await waitFor(() => expect(container.querySelectorAll('.recharts-pie-sector path').length).toBe(DATA.length))
    const sectors = container.querySelectorAll('.recharts-pie-sector path')
    expect(sectors[1]?.getAttribute('fill')).toBe('var(--chart-2)')
  })

  it('WHEN kind=bar-stacked THEN the bars share the stackId', async () => {
    barProps.length = 0
    draw('bar-stacked')

    await waitFor(() => expect(barProps.map((p) => p.dataKey)).toEqual(['orders', 'others']))
    expect(new Set(barProps.map((p) => p.stackId))).toEqual(new Set(['total']))
  })

  it('WHEN kind=bar-grouped THEN bars without stackId', async () => {
    barProps.length = 0
    draw('bar-grouped')

    await waitFor(() => expect(barProps.length).toBeGreaterThan(0))
    expect(barProps.every((p) => p.stackId === undefined)).toBe(true)
  })

  it('WHEN formatX and formatY THEN they are used on the axes', async () => {
    const formatY = vi.fn((v: number) => `${v} u`)
    const formatX = vi.fn((v: string) => `[${v}]`)
    draw('line', { formatX, formatY })

    await waitFor(() => expect(formatY).toHaveBeenCalled())
    expect(formatX).toHaveBeenCalled()
  })
})

const CURVES = [
  { age: 0, p3: 2.5, p50: 3.3, patient: 3.4 },
  { age: 1, p3: 3.4, p50: 4.5, patient: null },
  { age: 2, p3: 4.4, p50: 5.6, patient: 5.5 },
]

const drawCurves = (decimalsY?: number): void => {
  captured.lines.length = 0
  captured.axesX.length = 0
  captured.axesY.length = 0
  render(
    <UIChart
      kind="curves"
      data={CURVES}
      xKey="age"
      xDomain={[0, 15]}
      decimalsY={decimalsY}
      series={[
        { key: 'p3', label: 'P3', color: 5, stroke: 'dashed' },
        { key: 'p50', label: 'P50', color: 5, stroke: 'dotted' },
        { key: 'patient', label: 'Patient', color: 1, marker: 'circle', join: true },
      ]}
      ariaLabel="Weight for age"
    />,
  )
}

describe('UIChart kind="curves" [AC-8]', () => {
  it('WHEN kind=curves THEN numeric X axis with the given domain and figure', async () => {
    drawCurves()

    expect(await screen.findByRole('figure', { name: 'Weight for age' })).toBeTruthy()
    await waitFor(() => expect(captured.axesX[0]).toMatchObject({ type: 'number', dataKey: 'age', domain: [0, 15] }))
  })

  it('WHEN stroke and marker THEN strokeDasharray, dots and connectNulls per series', async () => {
    drawCurves()

    await waitFor(() => expect(captured.lines.length).toBeGreaterThanOrEqual(3))
    const [p3, p50, patient] = captured.lines
    expect(p3).toMatchObject({ strokeDasharray: '6 4', dot: false, connectNulls: false })
    expect(p50).toMatchObject({ strokeDasharray: '2 3' })
    expect(patient?.strokeDasharray).toBeUndefined()
    expect(patient?.dot).toMatchObject({ r: 4 })
    expect(patient?.connectNulls).toBe(true)
  })

  it('WHEN cross marker THEN draws a cross per data point', async () => {
    captured.lines.length = 0
    render(<UIChart kind="curves" data={CURVES} xKey="age" series={[{ key: 'patient', label: 'Patient', marker: 'cross' }]} ariaLabel="x" />)

    await waitFor(() => expect(captured.lines.length).toBeGreaterThan(0))
    const dot = captured.lines[0]?.dot as (p: { cx: number; cy: number; index: number }) => React.JSX.Element
    const { container } = render(<svg>{dot({ cx: 10, cy: 10, index: 0 })}</svg>)
    expect(container.querySelectorAll('path').length).toBe(1)
    expect(dot({ cx: Number.NaN, cy: 10, index: 1 })).toBeTruthy()
  })

  it('WHEN decimalsY=1 THEN the Y axis allows decimals and formats 85,7', async () => {
    drawCurves(1)

    await waitFor(() => expect(captured.axesY.length).toBeGreaterThan(0))
    const y = captured.axesY[0] as { allowDecimals: boolean; tickFormatter: (v: number) => string }
    expect(y.allowDecimals).toBe(true)
    expect(y.tickFormatter(85.7)).toBe('85,7')
  })

  it('WHEN kind=line THEN the Y axis stays without decimals', async () => {
    captured.axesY.length = 0
    draw('line')

    await waitFor(() => expect(captured.axesY.length).toBeGreaterThan(0))
    expect(captured.axesY[0]?.allowDecimals).toBe(false)
  })
})

const AUDIO = [
  { hz: 250, od: -10 },
  { hz: 500, od: 20 },
  { hz: 1000, od: 30 },
  { hz: 2000, od: 40 },
  { hz: 4000, od: 50 },
  { hz: 8000, od: 120 },
]
const TICKS_HZ = [250, 500, 1000, 2000, 4000, 8000]

// jsdom no dibuja los ticks de los ejes: se leen los vértices del trazo (un punto por frecuencia).
const vertices = (container: HTMLElement): { x: number; y: number }[] =>
  [...(container.querySelector('.recharts-line-curve')?.getAttribute('d') ?? '').matchAll(/[ML]([\d.]+),([\d.]+)/g)].map((m) => ({ x: Number(m[1]), y: Number(m[2]) }))

describe('UIChart curves with yInverted and xScale="log" [AC-9]', () => {
  it('WHEN yInverted and yDomain THEN the YAxis gets reversed and the domain, −10 above 120', async () => {
    captured.axesY.length = 0
    captured.axesX.length = 0
    const { container } = render(
      <UIChart kind="curves" data={AUDIO} xKey="hz" xScale="log" xTicks={TICKS_HZ} yInverted yDomain={[-10, 120]} series={[{ key: 'od', label: 'OD', marker: 'circle' }]} ariaLabel="Audiogram" />,
    )

    await waitFor(() => expect(captured.axesY.length).toBeGreaterThan(0))
    expect(captured.axesY[0]).toMatchObject({ reversed: true, domain: [-10, 120] })
    expect(captured.axesX[0]).toMatchObject({ scale: 'log', ticks: TICKS_HZ, domain: [250, 8000] })
    await waitFor(() => expect(vertices(container)).toHaveLength(AUDIO.length))
    const [a250, a500, , , a4000, a8000] = vertices(container).map((v) => ({ x: v.x, y: v.y }))
    const p = { a250: a250 ?? { x: 0, y: 0 }, a500: a500 ?? { x: 0, y: 0 }, a4000: a4000 ?? { x: 0, y: 0 }, a8000: a8000 ?? { x: 0, y: 0 } }
    // −10 dB (250 Hz) arriba de 120 dB (8000 Hz).
    expect(p.a250.y).toBeLessThan(p.a8000.y)
    expect(Math.abs(p.a500.x - p.a250.x - (p.a8000.x - p.a4000.x))).toBeLessThan(1)
  })

  it('WHEN curves without these props THEN linear axis without reversed', async () => {
    drawCurves()

    await waitFor(() => expect(captured.axesX.length).toBeGreaterThan(0))
    expect(captured.axesX[0]?.scale).toBe('auto')
    expect(captured.axesY[0]?.reversed).toBe(false)
  })
})

describe('UIChart motion [AC-17]', () => {
  const MOTION_KINDS: ChartKind[] = ['bar', 'bar-horizontal', 'line', 'area', 'donut']

  /** Dibuja cada forma, espera a que recharts las dibuje y devuelve las series animables capturadas. */
  const drawSeries = async (): Promise<Record<string, unknown>[]> => {
    resetCaptured()
    for (const kind of MOTION_KINDS) draw(kind)
    await waitFor(() => expect(screen.getAllByRole('figure').length).toBeGreaterThanOrEqual(MOTION_KINDS.length))
    return [...barProps, ...captured.lines, ...captured.areas, ...captured.pies]
  }

  it('WHEN reduced motion is requested THEN every series has isAnimationActive false [AC-17]', async () => {
    preferReducedMotion(true)

    const series = await drawSeries()

    expect(series.length).toBeGreaterThan(0)
    expect(series.every((props) => props.isAnimationActive === false)).toBe(true)
  })

  it('WHEN motion is allowed THEN every series has isAnimationActive true with 400 ms ease-out [AC-17]', async () => {
    preferReducedMotion(false)

    const series = await drawSeries()

    expect(series.length).toBeGreaterThan(0)
    for (const props of series) expect(props).toMatchObject({ isAnimationActive: true, animationDuration: 400, animationEasing: 'ease-out' })
  })

  it('WHEN the tooltip renders THEN its isAnimationActive is false [AC-17]', async () => {
    preferReducedMotion(false)
    resetCaptured()

    draw('line')
    draw('donut')

    await waitFor(() => expect(captured.tooltips.length).toBeGreaterThan(0))
    expect(captured.tooltips.every((props) => props.isAnimationActive === false)).toBe(true)
  })
})

describe('UIChart tooltipDetail [AC-7]', () => {
  const data = [{ date: '2026-11-08', value: 120 }]
  const series = [{ key: 'value', label: 'PA' }]
  type TooltipContent = (props: Record<string, unknown>) => React.ReactElement<{ children: React.ReactNode[] }>

  it('WHEN no tooltipDetail THEN the tooltip keeps the default content element', async () => {
    captured.tooltips.length = 0
    render(<UIChart kind="line" data={data} series={series} xKey="date" ariaLabel="PA" />)

    await waitFor(() => expect(captured.tooltips.length).toBeGreaterThan(0))
    expect(typeof captured.tooltips.at(-1)?.content).not.toBe('function')
  })

  it('WHEN tooltipDetail gives a line for the active point THEN the tooltip shows it under the values', async () => {
    captured.tooltips.length = 0
    render(<UIChart kind="line" data={data} series={series} xKey="date" ariaLabel="PA" tooltipDetail={(row) => `Original: ${row.date}`} />)

    await waitFor(() => expect(captured.tooltips.length).toBeGreaterThan(0))
    const content = captured.tooltips.at(-1)?.content as TooltipContent
    const element = content({ active: true, payload: [{ payload: data[0] }] })
    const detail = element.props.children[1] as React.ReactElement<{ children: string }>
    expect(detail.props.children).toBe('Original: 2026-11-08')
  })

  it('WHEN the tooltip is inactive or tooltipDetail gives nothing THEN no detail line is added', async () => {
    captured.tooltips.length = 0
    render(<UIChart kind="line" data={data} series={series} xKey="date" ariaLabel="PA" tooltipDetail={() => undefined} />)

    await waitFor(() => expect(captured.tooltips.length).toBeGreaterThan(0))
    const content = captured.tooltips.at(-1)?.content as TooltipContent
    const withoutValue = content({ active: true, payload: [{ payload: data[0] }] })
    const inactive = content({ active: false, payload: [] })
    expect(withoutValue.props.children[1]).toBeFalsy()
    expect(inactive.props.children[1]).toBeFalsy()
  })
})

describe('UIChart band [AC-7]', () => {
  it('WHEN band is given THEN a reference area spans the range with its label', async () => {
    captured.refAreas.length = 0
    draw('line', { band: { low: 3, high: 5.2, label: 'Meta' } })

    await waitFor(() => expect(captured.refAreas).toHaveLength(1))
    expect(captured.refAreas[0]).toMatchObject({ y1: 3, y2: 5.2 })
    expect(captured.refAreas[0]?.label).toMatchObject({ value: 'Meta' })
  })

  it('WHEN one bound is missing THEN the area reaches the edge of the data', async () => {
    captured.refAreas.length = 0
    draw('area', { band: { high: 5.2, label: 'Hasta' } })

    await waitFor(() => expect(captured.refAreas.length).toBeGreaterThan(0))
    expect(captured.refAreas[0]).toMatchObject({ y2: 5.2 })
    expect(typeof captured.refAreas[0]?.y1).toBe('number')
  })

  it('WHEN band is absent THEN no reference area renders', async () => {
    captured.refAreas.length = 0
    draw('line')

    await ready()
    expect(captured.refAreas).toHaveLength(0)
  })
})

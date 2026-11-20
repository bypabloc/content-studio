import { type KeyboardEvent, useEffect, useRef, useState } from 'react'

import { UIButton } from '../../atoms/UIButton'
import { UIField } from '../../molecules/UIField'
import { UIPopover } from '../../molecules/UIPopover'
import { UIText } from '../../atoms/UIText'

export * from './calendar'

import {
  clamp,
  fromIso,
  monthMatrix,
  monthStart,
  type PresetKey,
  pickDay,
  presetRange,
  previewRange,
  type Range,
  referenceDay,
  type Selection,
  shiftDay,
  toIso,
  weekEdge,
} from './calendar'
import { UIBox } from '../../atoms/UIBox'

/** Textos del selector, que la pantalla que lo usa toma de su catálogo. */
export type DateRangeLabels = {
  placeholder: string
  apply: string
  cancel: string
  clear: string
  previous: string
  next: string
  /** Etiquetas de los campos para escribir el inicio y el fin. */
  from: string
  to: string
  /** Duración del rango aplicado, en días (los dos extremos cuentan). */
  days: (count: number) => string
  presets: Record<PresetKey, string>
}

/** Atajos en el orden de la columna izquierda del panel. */
const PRESETS: PresetKey[] = ['today', 'yesterday', 'last7', 'last30', 'thisMonth', 'lastMonth']

/** Desplazamiento del foco por tecla: un día, una semana o el borde de la semana. */
const KEY_STEPS: Record<string, (iso: string) => string> = {
  ArrowLeft: (iso) => shiftDay(iso, -1),
  ArrowRight: (iso) => shiftDay(iso, 1),
  ArrowUp: (iso) => shiftDay(iso, -7),
  ArrowDown: (iso) => shiftDay(iso, 7),
  Home: (iso) => weekEdge(iso, 'start'),
  End: (iso) => weekEdge(iso, 'end'),
}

const monthTitle = (iso: string): string => new Intl.DateTimeFormat('es', { month: 'long', year: 'numeric', timeZone: 'UTC' }).format(fromIso(iso))
const longDate = (iso: string): string => new Intl.DateTimeFormat('es', { dateStyle: 'full', timeZone: 'UTC' }).format(fromIso(iso))
const mediumDate = (iso: string): string => new Intl.DateTimeFormat('es', { dateStyle: 'medium', timeZone: 'UTC' }).format(fromIso(iso))
const DAY_MS = 86_400_000
const lengthInDays = (range: Range): number => Math.round((fromIso(range.to).getTime() - fromIso(range.from).getTime()) / DAY_MS) + 1
const weekdayInitial = (iso: string): string => new Intl.DateTimeFormat('es', { weekday: 'narrow', timeZone: 'UTC' }).format(fromIso(iso))

/**
 * Selector de rango de fechas: dos meses consecutivos, seis atajos y un panel que se confirma con «Aplicar» (spec 126, AC-35).
 *
 * @author Pablo Contreras
 * @since 2026/10/31
 *
 * @param props.value - Rango aplicado, o `null` si no hay filtro.
 * @param props.onChange - Recibe el rango al aplicar o `null` al limpiar.
 * @param props.min - Primer día que se puede elegir, si lo hay.
 * @param props.max - Último día que se puede elegir, si lo hay.
 * @param props.today - Día de referencia para los atajos; por defecto, hoy.
 * @param props.labels - Textos del selector.
 * @returns Disparador con el rango aplicado y su panel.
 */
export function UIDateRangePicker({
  value,
  onChange,
  min,
  max,
  today,
  labels,
}: {
  value: Range | null
  onChange: (value: Range | null) => void
  min?: string
  max?: string
  today?: Date
  labels: DateRangeLabels
}): React.JSX.Element {
  const triggerRef = useRef<HTMLButtonElement>(null)
  const gridRef = useRef<HTMLDivElement>(null)
  const moveFocus = useRef(false)
  const [open, setOpen] = useState(false)
  const [draft, setDraft] = useState<Selection>({ from: null, to: null })
  const [hover, setHover] = useState<string | null>(null)
  const [view, setView] = useState('')
  const [cursor, setCursor] = useState('')
  const [preset, setPreset] = useState<PresetKey | null>(null)

  useEffect(() => {
    if (!moveFocus.current) return
    moveFocus.current = false
    gridRef.current?.querySelector<HTMLElement>(`[data-iso="${cursor}"]`)?.focus()
  }, [cursor])

  const openPanel = (): void => {
    const start = value?.from ?? toIso(referenceDay(today))
    setDraft({ from: value?.from ?? null, to: value?.to ?? null })
    setPreset(null)
    setView(monthStart(start, 0))
    setCursor(start)
    setOpen(true)
  }

  const applyPreset = (key: PresetKey): void => {
    const range = clamp(presetRange(key, referenceDay(today)), min, max)
    setDraft({ from: range.from, to: range.to })
    setPreset(key)
    setCursor(range.to)
    setView(monthStart(range.to, -1))
  }

  const pick = (iso: string): void => {
    setDraft((current) => pickDay(current, iso))
    setPreset(null)
    setCursor(iso)
  }

  /** Fecha escrita a mano: si queda antes del inicio (o después del fin), los extremos se intercambian. */
  const type = (field: 'from' | 'to', iso: string): void => {
    setPreset(null)
    setDraft((current) => {
      const next = { ...current, [field]: iso || null }
      return next.from !== null && next.to !== null && next.from > next.to ? { from: next.to, to: next.from } : next
    })
    if (iso) {
      setCursor(iso)
      setView(monthStart(iso, 0))
    }
  }

  const moveCursor = (event: KeyboardEvent<HTMLButtonElement>, iso: string): void => {
    const step = KEY_STEPS[event.key]
    if (!step) return
    event.preventDefault()
    const next = step(iso)
    moveFocus.current = true
    setCursor(next)
    if (next < view || next >= monthStart(view, 2)) setView(monthStart(next, 0))
  }

  const apply = (): void => {
    if (draft.from !== null && draft.to !== null) onChange({ from: draft.from, to: draft.to })
    setOpen(false)
  }

  const preview = previewRange(draft, hover)
  const stateOf = (iso: string): string | undefined => {
    if (iso === draft.from) return 'start'
    if (iso === draft.to) return 'end'
    if (draft.from !== null && draft.to !== null && iso > draft.from && iso < draft.to) return 'between'
    if (preview !== null && iso >= preview.from && iso <= preview.to) return 'preview'
    return undefined
  }

  const renderDay = (iso: string, inMonth: boolean): React.JSX.Element => {
    const disabled = (min !== undefined && iso < min) || (max !== undefined && iso > max)
    const state = stateOf(iso)
    const selected = state === 'start' || state === 'end'
    // El tramo intermedio va sobre un tinte del primario con texto normal: `bg-accent` no llegaba a 4,5:1 en claro.
    const tone = selected ? 'bg-primary text-primary-foreground' : state ? 'bg-primary/15 text-foreground' : 'hover:bg-muted'
    return (
      <UIBox key={iso} role="gridcell" className="grid place-items-center">
        <UIButton
          variant="ghost"
          data-iso={iso}
          data-state={state}
          aria-label={longDate(iso)}
          aria-pressed={selected || undefined}
          tabIndex={iso === cursor && inMonth ? 0 : -1}
          disabled={disabled}
          onClick={() => pick(iso)}
          onKeyDown={(event) => moveCursor(event, iso)}
          onMouseEnter={() => setHover(iso)}
          onMouseLeave={() => setHover(null)}
          className={`ui-focus size-10 min-h-10 px-0 font-normal rounded-lg text-sm tabular-nums motion-safe:transition-colors disabled:opacity-40 ${tone} ${inMonth ? 'text-foreground' : 'text-muted-foreground'}`}
        >
          {fromIso(iso).getUTCDate()}
        </UIButton>
      </UIBox>
    )
  }

  const renderMonth = (monthIso: string, index: number): React.JSX.Element => {
    const weeks = monthMatrix(fromIso(monthIso).getUTCFullYear(), fromIso(monthIso).getUTCMonth())
    const monthKey = monthIso.slice(0, 7)
    return (
      // En el teléfono solo cabe un mes: el segundo aparece desde `sm`.
      <UIBox key={monthIso} className={`min-w-72 flex-col gap-2 ${index === 0 ? 'flex' : 'hidden sm:flex'}`}>
        <UIBox className="flex h-11 items-center justify-center">
          <UIText variant="heading">{monthTitle(monthIso)}</UIText>
        </UIBox>
        <UIBox role="grid" aria-label={monthTitle(monthIso)} className="flex flex-col gap-1">
          <UIBox role="row" className="grid grid-cols-7 gap-1">
            {(weeks[0] ?? []).map((iso) => (
              <UIBox as="span" key={iso} role="columnheader" className="grid size-10 place-items-center text-xs text-muted-foreground">
                {weekdayInitial(iso)}
              </UIBox>
            ))}
          </UIBox>
          {weeks.map((week) => (
            <UIBox key={week[0]} role="row" className="grid grid-cols-7 gap-1">
              {week.map((iso) => renderDay(iso, iso.slice(0, 7) === monthKey))}
            </UIBox>
          ))}
        </UIBox>
      </UIBox>
    )
  }

  const renderPanel = (): React.JSX.Element => (
    <UIBox data-range-panel className="max-w-2xl">
      <UIBox className="flex flex-col gap-4 p-2 sm:flex-row">
        <UIBox className="flex flex-row flex-wrap gap-1 sm:flex-col">
          {PRESETS.map((key) => (
            <UIButton
              key={key}
              variant="ghost"
              aria-pressed={preset === key}
              className={preset === key ? 'bg-primary/15 text-foreground' : undefined}
              onClick={() => applyPreset(key)}
            >
              {labels.presets[key]}
            </UIButton>
          ))}
        </UIBox>
        <UIBox className="flex flex-col gap-3">
          <UIBox className="grid grid-cols-2 gap-2">
            <UIField type="date" label={labels.from} value={draft.from ?? ''} min={min} max={max} onChange={(event) => type('from', event.target.value)} />
            <UIField type="date" label={labels.to} value={draft.to ?? ''} min={min} max={max} onChange={(event) => type('to', event.target.value)} />
          </UIBox>
          {/* Los botones de mes van en los bordes del bloque: en el teléfono, «Avanzar» queda junto al único mes visible. */}
          <UIBox ref={gridRef} className="relative flex gap-4">
            <UIButton variant="ghost" icon="chevron-left" aria-label={labels.previous} className="absolute top-0 left-0" onClick={() => setView(monthStart(view, -1))} />
            {[0, 1].map((index) => renderMonth(monthStart(view, index), index))}
            <UIButton variant="ghost" icon="chevron-right" aria-label={labels.next} className="absolute top-0 right-0" onClick={() => setView(monthStart(view, 1))} />
          </UIBox>
        </UIBox>
      </UIBox>
      <UIBox className="flex justify-end gap-2 p-2">
        <UIButton variant="ghost" onClick={() => setOpen(false)}>
          {labels.cancel}
        </UIButton>
        <UIButton disabled={draft.from === null || draft.to === null} onClick={apply}>
          {labels.apply}
        </UIButton>
      </UIBox>
    </UIBox>
  )

  return (
    <UIBox className="inline-flex items-center gap-2">
      <UIButton
        ref={triggerRef}
        variant="secondary"
        icon="calendar-range"
        aria-haspopup="dialog"
        aria-expanded={open}
        onClick={() => (open ? setOpen(false) : openPanel())}
      >
        {value ? `${mediumDate(value.from)} – ${mediumDate(value.to)} · ${labels.days(lengthInDays(value))}` : labels.placeholder}
      </UIButton>
      {value ? <UIButton variant="ghost" icon="x" aria-label={labels.clear} onClick={() => onChange(null)} /> : null}
      <UIPopover anchor={triggerRef} open={open} onOpenChange={(next) => (next ? openPanel() : setOpen(false))} label={labels.placeholder} align="start">
        {open ? renderPanel() : null}
      </UIPopover>
    </UIBox>
  )
}

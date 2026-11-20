import { useState } from 'react'

import { UIButton } from '../../atoms/UIButton'
import { UIField } from '../UIField'
import { UIBox } from '../../atoms/UIBox'

/** Quick filter range. */
export type RangePreset = '30d' | '90d' | '12m' | 'year'

/** Date range in local ISO `YYYY-MM-DD` (both ends included). */
export type Range = { from: string; to: string }

const PRESETS: RangePreset[] = ['30d', '90d', '12m', 'year']

const pad = (n: number): string => String(n).padStart(2, '0')

/**
 * Browser's local date as `YYYY-MM-DD` (not UTC: at 21:00 local time
 * west of UTC it is still the same day).
 */
export function aIso(date: Date): string {
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`
}

/**
 * Range of a preset ending today: 30 or 90 days ago, the same day of the previous
 * year (`12m`; a February 29th falls on March 1st) or January 1st of the
 * current year (`year`).
 */
export function presetRange(preset: RangePreset, today: Date): Range {
  const [y, m, d] = [today.getFullYear(), today.getMonth(), today.getDate()]
  const from = { '30d': new Date(y, m, d - 30), '90d': new Date(y, m, d - 90), '12m': new Date(y - 1, m, d), year: new Date(y, 0, 1) }[preset]
  return { from: aIso(from), to: aIso(new Date(y, m, d)) }
}

type Props = {
  from: string
  to: string
  onChange: (from: string, to: string) => void
  /** Cada edición a mano, también la inválida (sin llamar a `onChange`). */
  onEdit?: (range: Range) => void
  today?: Date
  /** Días máximos entre desde y hasta (el límite del server); más largo muestra `labels.tooLong` y no llama a `onChange`. */
  maxDays?: number
  labels: { from: string; to: string; presets: string; '30d': string; '90d': string; '12m': string; year: string; error: string; tooLong?: string }
}

/** Días entre dos fechas `YYYY-MM-DD`. */
const daysBetween = (from: string, to: string): number => Math.round((Date.parse(`${to}T00:00:00Z`) - Date.parse(`${from}T00:00:00Z`)) / 86_400_000)

/**
 * Date range filter: presets (buttons with `aria-pressed` that apply
 * instantly) and two `<input type="date">`. A valid change (both dates and
 * `to >= from`) calls `onChange`; if `to < from` it shows the error
 * next to "to" and doesn't call it. `onEdit` hears every hand edit. The local draft resynchronizes when
 * the props change.
 *
 * @author Pablo Contreras
 * @since 2026/09/28
 * @since 2026/11/19
 */
export function UIDateRangeFilter({ from, to, onChange, onEdit, today: todayProp, maxDays, labels }: Props): React.JSX.Element {
  const [today] = useState(() => todayProp ?? new Date())
  const [draft, setDraft] = useState<Range>({ from, to })
  const [synced, setSynced] = useState<Range>({ from, to })
  if (synced.from !== from || synced.to !== to) {
    setSynced({ from, to })
    setDraft({ from, to })
  }

  const edit = (field: keyof Range, value: string): void => {
    const next = { ...draft, [field]: value }
    setDraft(next)
    onEdit?.(next)
    const tooLong = maxDays !== undefined && next.from && next.to && daysBetween(next.from, next.to) > maxDays
    if (next.from && next.to && next.to >= next.from && !tooLong) onChange(next.from, next.to)
  }
  const invalid = Boolean(draft.from && draft.to && draft.to < draft.from)
  const tooLong = !invalid && maxDays !== undefined && Boolean(draft.from && draft.to) && daysBetween(draft.from, draft.to) > maxDays
  const error = invalid ? labels.error : tooLong ? (labels.tooLong ?? labels.error) : undefined

  return (
    <UIBox className="flex w-full flex-col gap-4 lg:flex-row lg:items-end">
      <UIBox role="group" aria-label={labels.presets} className="flex flex-wrap gap-2">
        {PRESETS.map((preset) => {
          const range = presetRange(preset, today)
          const pressed = range.from === from && range.to === to
          return (
            <UIButton key={preset} variant={pressed ? 'primary' : 'secondary'} aria-pressed={pressed} onClick={() => onChange(range.from, range.to)}>
              {labels[preset]}
            </UIButton>
          )
        })}
      </UIBox>
      <UIBox className="grid w-full gap-3 sm:grid-cols-2 lg:max-w-md">
        <UIField type="date" label={labels.from} value={draft.from} onChange={(e) => edit('from', e.target.value)} />
        <UIField type="date" label={labels.to} value={draft.to} error={error} onChange={(e) => edit('to', e.target.value)} />
      </UIBox>
    </UIBox>
  )
}

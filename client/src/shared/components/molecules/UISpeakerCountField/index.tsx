import { useState } from 'react'

import { t } from '@/shared/i18n/t'

import { UIStack } from '../../atoms/UIStack'
import { UIField } from '../UIField'
import { UISelect } from '../UISelect'

/** Hablantes que pide un trabajo que identifica hablantes: ninguno (automático), uno exacto o un rango (spec 036, D-4). */
export type SpeakerCounts = { num_speakers?: number; min_speakers?: number; max_speakers?: number }

type Mode = 'auto' | 'exact' | 'range'
const MIN_SPEAKERS = 1
const MAX_SPEAKERS = 20

function whole(value: string): number | null {
  const number = Number(value)
  return Number.isInteger(number) && number >= MIN_SPEAKERS && number <= MAX_SPEAKERS ? number : null
}

/** Lo que el trabajo pide para ese modo y esos números; null si aún no es válido. */
function countsOf(mode: Mode, exact: string, min: string, max: string): SpeakerCounts | null {
  if (mode === 'auto') return {}
  if (mode === 'exact') {
    const number = whole(exact)
    return number === null ? null : { num_speakers: number }
  }
  const low = whole(min)
  const high = whole(max)
  return low === null || high === null || low > high ? null : { min_speakers: low, max_speakers: high }
}

/**
 * Cuántos hablantes hay: automático, exacto o entre dos cifras, del 1 al 20. Emite lo que el trabajo debe pedir
 * (`{num_speakers}`, `{min_speakers, max_speakers}` o `{}`) solo cuando es válido.
 */
export function UISpeakerCountField({
  onChange,
  disabled = false,
}: {
  onChange: (counts: SpeakerCounts) => void
  disabled?: boolean
}): React.JSX.Element {
  const [mode, setMode] = useState<Mode>('auto')
  const [exact, setExact] = useState('')
  const [min, setMin] = useState('')
  const [max, setMax] = useState('')
  const typed = [exact, min, max].some((value) => value !== '')

  function emit(next: { mode?: Mode; exact?: string; min?: string; max?: string }): void {
    const counts = countsOf(next.mode ?? mode, next.exact ?? exact, next.min ?? min, next.max ?? max)
    if (counts !== null) onChange(counts)
  }
  const invalid = typed && countsOf(mode, exact, min, max) === null

  return (
    <UIStack gap="md">
      <UISelect
        label={t('speakers.count.label')}
        disabled={disabled}
        value={mode}
        options={[
          { value: 'auto', label: t('speakers.count.auto') },
          { value: 'exact', label: t('speakers.count.exact') },
          { value: 'range', label: t('speakers.count.range') },
        ]}
        onChange={(value) => {
          setMode(value as Mode)
          emit({ mode: value as Mode })
        }}
      />
      {mode === 'exact' ? (
        <UIField
          label={t('speakers.count.number')}
          type="number"
          min={MIN_SPEAKERS}
          max={MAX_SPEAKERS}
          value={exact}
          disabled={disabled}
          error={invalid ? t('error.invalid_speakers') : undefined}
          onChange={(event) => {
            setExact(event.target.value)
            emit({ exact: event.target.value })
          }}
        />
      ) : null}
      {mode === 'range' ? (
        <UIStack direction="row" gap="md">
          <UIStack className="min-w-0 flex-1">
            <UIField
              label={t('speakers.count.min')}
              type="number"
              min={MIN_SPEAKERS}
              max={MAX_SPEAKERS}
              value={min}
              disabled={disabled}
              onChange={(event) => {
                setMin(event.target.value)
                emit({ min: event.target.value })
              }}
            />
          </UIStack>
          <UIStack className="min-w-0 flex-1">
            <UIField
              label={t('speakers.count.max')}
              type="number"
              min={MIN_SPEAKERS}
              max={MAX_SPEAKERS}
              value={max}
              disabled={disabled}
              error={invalid ? t('error.invalid_speakers') : undefined}
              onChange={(event) => {
                setMax(event.target.value)
                emit({ max: event.target.value })
              }}
            />
          </UIStack>
        </UIStack>
      ) : null}
    </UIStack>
  )
}

import { useId } from 'react'
import { UIField } from '../UIField'
import { UIBox } from '../../atoms/UIBox'
import { UIText } from '../../atoms/UIText'

type Parts = { day: string; month: string; year: string }
type Props = {
  label: string
  labels: Parts
  values: Parts
  onChange: (part: keyof Parts, value: string) => void
}

const PARTS = ['day', 'month', 'year'] as const

/**
 * Fecha en tres campos numéricos (día, mes y año) dentro de un grupo nombrado por su título visible. Es controlado y
 * avisa qué parte cambió. El grupo es un `role="group"` y no un `fieldset`: `aria-labelledby` lo nombra con el título.
 *
 * @author Pablo Contreras
 * @since 2026/11/10
 * @since 2026/11/19
 */
export function UIDateParts({ label, labels, values, onChange }: Props): React.JSX.Element {
  const titleId = useId()
  return (
    <UIBox role="group" aria-labelledby={titleId} className="flex flex-col gap-2">
      <UIText id={titleId} variant="caption" className="font-bold text-foreground-secondary">
        {label}
      </UIText>
      <UIBox className="grid grid-cols-3 gap-2">
        {PARTS.map((part) => (
          <UIField
            key={part}
            label={labels[part]}
            inputMode="numeric"
            value={values[part]}
            onChange={(event) => onChange(part, event.target.value)}
          />
        ))}
      </UIBox>
    </UIBox>
  )
}

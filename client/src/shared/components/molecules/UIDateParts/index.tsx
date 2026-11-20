import { UIField } from '../UIField'
import { UIBox } from '../../atoms/UIBox'

type Parts = { day: string; month: string; year: string }
type Props = {
  label: string
  labels: Parts
  values: Parts
  onChange: (part: keyof Parts, value: string) => void
}

const PARTS = ['day', 'month', 'year'] as const

/**
 * Fecha en tres campos numéricos (día, mes y año) dentro de un `fieldset`
 * nombrado por su leyenda. Es controlado y avisa qué parte cambió.
 *
 * @author Pablo Contreras
 * @since 2026/11/10
 * @since 2026/11/19
 */
export function UIDateParts({ label, labels, values, onChange }: Props): React.JSX.Element {
  return (
    <fieldset className="flex flex-col gap-2">
      <legend className="ui-typography-caption font-bold text-foreground-secondary">{label}</legend>
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
    </fieldset>
  )
}

import { UIBadge } from '../../atoms/UIBadge'
import type { IconName } from '../../atoms/UIIcon'
import { UIText } from '../../atoms/UIText'
import { UIBox } from '../../atoms/UIBox'

type Tone = 'neutral' | 'brand' | 'accent'
type Props = { label: string; steps: string[]; current: number }

/**
 * Tono de cada paso: los anteriores al actual van en `accent`, el actual en
 * `brand` y los siguientes en `neutral`.
 *
 * @author Pablo Contreras
 * @since 2026/11/10
 * @since 2026/11/19
 */
function toneOf(index: number, current: number): Tone {
  if (index < current) return 'accent'
  if (index === current) return 'brand'
  return 'neutral'
}

/** Ícono de cada paso: completado, actual y pendiente, el mismo vocabulario que la lista de secciones. */
function iconOf(index: number, current: number): IconName {
  if (index < current) return 'circle-check'
  if (index === current) return 'pencil'
  return 'clock'
}

/**
 * Progreso de pasos en una lista nombrada. El paso actual lleva
 * `aria-current="step"`; los anteriores quedan en tono de completado.
 *
 * @author Pablo Contreras
 * @since 2026/11/10
 * @since 2026/11/19
 */
export function UIStepProgress({ label, steps, current }: Props): React.JSX.Element {
  return (
    <UIBox role="list" aria-label={label} className="flex flex-wrap gap-3">
      {steps.map((step, index) => (
        <UIBox role="listitem" key={step} aria-current={index === current ? 'step' : undefined} className="flex items-center gap-2">
          <UIBadge tone={toneOf(index, current)} icon={iconOf(index, current)}>{index + 1}</UIBadge>
          <UIText variant="caption">{step}</UIText>
        </UIBox>
      ))}
    </UIBox>
  )
}

import { useRecommendedValue } from '@/shared/hooks/useRecommendedValue'
import { t } from '@/shared/i18n/t'

import { UISelect, type UISelectOption } from '../UISelect'

export interface SelectOption {
  value: string
  label: string
  recommended?: boolean
  disabled?: boolean
  hint?: string
}

/**
 * Un selector que recuerda la última elección (en settings, con la clave `settingKey`). Sin elección guardada, o si la
 * guardada ya no existe, vale la recomendada, marcada con ★ (AC-3). Con `beforeChange`, la elección solo se aplica
 * si esa función responde que sí (la licencia de un motor, AC-7); si no, el selector sigue en la opción anterior.
 * Se compone sobre `UISelect` (spec 008, D-3): la pista de cada opción va como su descripción.
 *
 * @author Pablo Contreras
 * @since 2026/11/19
 */
export function UIRecommendedSelect({
  settingKey,
  label,
  options,
  onChange,
  beforeChange,
}: {
  settingKey: string
  label: string
  options: readonly SelectOption[]
  onChange?: (value: string) => void
  beforeChange?: (value: string) => Promise<boolean>
}): React.JSX.Element {
  const [value, setStored] = useRecommendedValue(settingKey, options)
  const choose = (next: string) => {
    setStored(next)
    onChange?.(next)
  }
  const items: UISelectOption[] = options.map((option) => ({
    value: option.value,
    label: option.recommended ? `★ ${option.label}` : option.label,
    // La recomendada dice «Recomendado» y, si trae pista (p. ej. el tamaño de un modelo), la sigue con ella.
    description: [option.recommended ? t('select.recommended') : null, option.hint].filter(Boolean).join(' · ') || undefined,
    disabled: option.disabled,
  }))

  return (
    <UISelect
      label={label}
      options={items}
      value={value}
      onChange={(next) => {
        if (beforeChange) void beforeChange(next).then((allowed) => allowed && choose(next))
        else choose(next)
      }}
    />
  )
}

import { cn } from 'cn'

type Props = {
  label: string
  value: string
  name?: string
  hiddenValue?: string
  className?: string
  hideLabel?: boolean
}

/**
 * Muestra una opción única como valor fijo no editable en un par término/definición (`dl`),
 * preservando el campo oculto con `name` para que los formularios envíen el valor.
 *
 * @author Pablo Contreras
 * @since 2026/09/29
 */
export function UIFixedValue({ label, value, name, hiddenValue, className, hideLabel }: Props): React.JSX.Element {
  return (
    <dl className={cn('flex flex-col gap-1', className)}>
      <dt className={cn('ui-typography-caption font-bold text-foreground-secondary', hideLabel && 'sr-only')}>{label}</dt>
      <dd className="ui-typography-body font-bold text-foreground">{value}</dd>
      {name ? <input type="hidden" name={name} value={hiddenValue ?? value} /> : null}
    </dl>
  )
}

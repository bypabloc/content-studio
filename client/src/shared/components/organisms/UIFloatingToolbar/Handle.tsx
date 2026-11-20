import { cn } from 'cn'

import { UIBox } from '../../atoms/UIBox'
import { UIButton } from '../../atoms/UIButton'

type Props = {
  /** Nombre accesible del asa: el texto que pide la pantalla por props. */
  label: string
  /** Clases de la posición del asa, según la ubicación de la barra. */
  className: string
  vertical: boolean
  /** Vuelve a mostrar la barra; con `focusFirst`, lleva el foco a su primera acción. */
  onReveal: (focusFirst?: boolean) => void
}

/**
 * Asa de la barra cuando está oculta: un botón redondeado con una raya visual. Al pasar el puntero, enfocarlo o pulsarlo,
 * vuelve a mostrar la barra.
 *
 * @author Pablo Contreras
 * @since 2026/11/19
 */
export function FloatingToolbarHandle({ label, className, vertical, onReveal }: Props): React.JSX.Element {
  return (
    <UIButton
      variant="ghost"
      aria-label={label}
      className={cn('absolute z-50 flex min-h-11 min-w-11 items-center justify-center rounded-full bg-card px-0 shadow-ui-lg hover:bg-card focus-visible:ui-focus', className)}
      onPointerEnter={() => onReveal()}
      onFocus={() => onReveal(true)}
      onClick={() => onReveal(true)}
    >
      <UIBox as="span" aria-hidden="true" className={cn('h-1.5 w-12 rounded-full bg-border', vertical && 'h-12 w-1.5')} />
    </UIButton>
  )
}

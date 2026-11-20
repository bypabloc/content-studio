import type { ComponentProps } from 'react'

import type { IconName } from '../../atoms/UIIcon'
import { UIButton } from '../../atoms/UIButton'
import { UITooltip } from '../../atoms/UITooltip'

type Props = Omit<ComponentProps<typeof UIButton>, 'children' | 'icon' | 'aria-label'> & {
  icon: IconName
  /** Nombre accesible y texto de ayuda: el ícono solo no se explica por sí mismo. */
  label: string
  /** Botón de alternar: expone `aria-pressed`. Sin él, no es un botón de estado. */
  pressed?: boolean
  /** Atajo de teclado que se muestra junto al texto de ayuda. */
  shortcut?: string
}

/**
 * Botón de solo ícono: `label` es su nombre accesible y su texto de ayuda, que
 * aparece al pasar el ratón (tras la demora) o al enfocarlo, con `shortcut` si lo
 * tiene. Con `pressed` es un botón de alternar. Área táctil de 44 px.
 *
 * @author Pablo Contreras
 * @since 2026/11/19
 */
export function UIIconButton({ icon, label, pressed, shortcut, variant = 'ghost', className, ...props }: Props): React.JSX.Element {
  return (
    <UITooltip content={label} shortcut={shortcut}>
      <UIButton
        variant={variant}
        icon={icon}
        aria-label={label}
        aria-pressed={pressed}
        className={className ?? 'size-11 px-0'}
        {...props}
      />
    </UITooltip>
  )
}

import { Button } from '../../shadcn/button'

import { type IconName, UIIcon } from '../../atoms/UIIcon'
import { UIIconButton } from '../UIIconButton'

/** Preferencia de tema: claro, oscuro o la del sistema. */
export type Theme = 'light' | 'dark' | 'system'

/** Preferencia válida a partir de lo que guarda la app (`ui.theme`); desconocida o sin cargar → `system`. */
export function toTheme(value: string | undefined): Theme {
  return value === 'light' || value === 'dark' ? value : 'system'
}

/** Ícono de cada preferencia de tema (spec 009, D-2). */
export const THEME_ICONS: Record<Theme, IconName> = { light: 'theme-light', dark: 'theme-dark', system: 'theme-system' }

const NEXT: Record<Theme, Theme> = { light: 'dark', dark: 'system', system: 'light' }

/** Preferencia siguiente del ciclo claro → oscuro → sistema → claro. */
export function nextTheme(theme: Theme): Theme {
  return NEXT[theme]
}

type Props = { theme: Theme; onThemeChange: (theme: Theme) => void; labels: { toggle: string }; visibleLabel?: string }

/**
 * Selector de tema de un solo botón: cada clic pasa a la preferencia
 * siguiente (claro → oscuro → sistema). El ícono muestra la actual;
 * `labels.toggle` es su nombre accesible y su texto de ayuda. El shell lo arma
 * con `theme.change`, que dice el modo actual y el siguiente. Sin `visibleLabel`
 * es un `UIIconButton` (spec 009, D-4); con `visibleLabel` muestra un texto corto
 * junto al ícono (p. ej. en la barra del portal) y el nombre accesible sigue siendo
 * `labels.toggle`.
 * Es un componente controlado: el shell lee y guarda la preferencia con
 * `useTheme` (`shared/theme`), así la molécula no depende de la API de settings
 * (spec 008, D-7).
 *
 * @author Pablo Contreras
 * @since 2026/09/27
 * @since 2026/11/19
 */
export function UIThemeToggle({ theme, onThemeChange, labels, visibleLabel }: Props): React.JSX.Element {
  const onClick = () => onThemeChange(nextTheme(theme))
  if (visibleLabel) {
    return (
      <Button
        variant="outline"
        aria-label={labels.toggle}
        onClick={onClick}
        className="min-h-11 cursor-pointer rounded-xl bg-card px-4 font-bold focus-visible:ui-focus"
      >
        <UIIcon name={THEME_ICONS[theme]} className="size-5" />
        {visibleLabel}
      </Button>
    )
  }
  return <UIIconButton variant="secondary" icon={THEME_ICONS[theme]} label={labels.toggle} onClick={onClick} />
}

import { Button } from '../../shadcn/button'

import { type IconName, UIIcon } from '../../atoms/UIIcon'
import { UIBox } from '../../atoms/UIBox'

/** Preferencia de tema: claro, oscuro o la del sistema. */
export type Theme = 'light' | 'dark' | 'system'

/** Preferencia válida a partir de lo que guarda la app (`ui.theme`); desconocida o sin cargar → `system`. */
export function toTheme(value: string | undefined): Theme {
  return value === 'light' || value === 'dark' ? value : 'system'
}

/** Textos de las opciones de tema (del catálogo i18n). */
export type ThemeLabels = { light: string; dark: string; system: string }

/** Ícono de cada preferencia de tema. */
export const THEME_ICONS: Record<Theme, IconName> = { light: 'sun', dark: 'moon', system: 'monitor' }

const NEXT: Record<Theme, Theme> = { light: 'dark', dark: 'system', system: 'light' }

/** Preferencia siguiente del ciclo claro → oscuro → sistema → claro. */
export function nextTheme(theme: Theme): Theme {
  return NEXT[theme]
}

type Props = { theme: Theme; onThemeChange: (theme: Theme) => void; labels: ThemeLabels & { toggle: string }; visibleLabel?: string }

/**
 * Selector de tema de un solo botón: cada clic pasa a la preferencia
 * siguiente (claro → oscuro → sistema). El ícono muestra la actual;
 * `labels.toggle` lo nombra y la preferencia actual lo describe.
 * `visibleLabel` muestra un texto corto junto al ícono (p. ej. en la barra del
 * portal); el nombre accesible sigue siendo `labels.toggle`.
 * Es un componente controlado: el shell lee y guarda la preferencia con
 * `useTheme` (`shared/theme`), así la molécula no depende de la API de settings
 * (spec 008, D-7).
 *
 * @author Pablo Contreras
 * @since 2026/09/27
 * @since 2026/11/19
 */
export function UIThemeToggle({ theme, onThemeChange, labels, visibleLabel }: Props): React.JSX.Element {
  return (
    <Button
      variant="outline"
      size={visibleLabel ? 'default' : 'icon'}
      title={labels[theme]}
      aria-label={visibleLabel ? labels.toggle : undefined}
      onClick={() => onThemeChange(nextTheme(theme))}
      className={visibleLabel ? 'min-h-11 cursor-pointer rounded-xl bg-card px-4 font-bold focus-visible:ui-focus' : 'size-11 cursor-pointer rounded-xl bg-card focus-visible:ui-focus'}
    >
      <UIIcon name={THEME_ICONS[theme]} className="size-5" />
      {visibleLabel ? visibleLabel : <UIBox as="span" className="sr-only">{labels.toggle}</UIBox>}
    </Button>
  )
}

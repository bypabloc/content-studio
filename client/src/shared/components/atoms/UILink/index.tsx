import { cn } from 'cn'
import type { ComponentProps } from 'react'

import { type IconName, UIIcon } from '../UIIcon'

const BASE = 'focus-visible:ui-focus'
const ACTION = 'ui-typography-body inline-flex min-h-11 cursor-pointer items-center justify-center gap-2 rounded-xl px-4 font-bold shadow-ui ui-press'
const VARIANTS = {
  primary: `${ACTION} bg-primary text-primary-foreground hover:bg-primary-hover`,
  secondary: `${ACTION} border border-border bg-card text-foreground hover:border-input hover:bg-muted`,
  inline: 'inline-flex items-center gap-1.5 rounded-sm font-bold text-accent-foreground underline-offset-4 hover:underline',
} as const

type Props = ComponentProps<'a'> & {
  variant?: keyof typeof VARIANTS
  icon?: IconName
  hideLabelOnMobile?: boolean
  // Aviso que se anuncia tras el texto (p. ej. «(se abre en una pestaña nueva)») sin mostrarse.
  newTab?: string
}

/**
 * Enlace de navegación interna: una `<a>` con `href` de hash (`#/<sección>`), porque el
 * router de content-studio es por hash (spec 008, D-3). Las páginas y el shell lo usan en vez de escribir `<a>`. Con
 * `variant` luce como acción (`primary`/`secondary`, área táctil de 44px) o
 * enlace destacado (`inline`), con foco visible e ícono decorativo opcional.
 * Las variantes de acción se reducen al pulsar (`motion-safe`); la inline no.
 * `hideLabelOnMobile` (con una variante de acción) deja solo el ícono en
 * mobile; el texto sigue siendo el nombre accesible, como en `UIButton`.
 * Para un enlace externo que abre otra pestaña (`target="_blank"`), `newTab`
 * añade el aviso solo para lectores de pantalla.
 *
 * @author Pablo Contreras
 * @since 2026/09/27
 * @since 2026/11/19
 */
export function UILink({ variant, icon, hideLabelOnMobile = false, newTab, className, children, ...props }: Props): React.JSX.Element {
  return (
    <a className={variant ? cn(VARIANTS[variant], BASE, hideLabelOnMobile && 'max-sm:w-11 max-sm:px-0', className) : className} {...props}>
      {icon ? <UIIcon name={icon} /> : null}
      {hideLabelOnMobile ? <span className="max-sm:sr-only">{children}</span> : children}
      {newTab ? <>{' '}<span className="sr-only">{newTab}</span></> : null}
    </a>
  )
}

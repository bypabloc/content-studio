import { cn } from 'cn'
import type { ComponentProps } from 'react'

import { Button } from '../../shadcn/button'

import { type IconName, UIIcon } from '../UIIcon'

const VARIANTS = { primary: 'default', secondary: 'outline', ghost: 'ghost', danger: 'destructive' } as const

const TONE = {
  primary: 'shadow-ui hover:bg-primary-hover',
  secondary: 'bg-card text-foreground shadow-ui hover:border-input hover:bg-muted',
  ghost: 'text-foreground-secondary hover:text-foreground',
  // Confirmación destructiva: rojo sólido; `text-card` es blanco en claro y oscuro en tema oscuro (contraste AA en ambos).
  danger: 'bg-destructive text-card shadow-ui hover:bg-destructive/90 focus-visible:border-destructive dark:bg-destructive dark:hover:bg-destructive/90',
} as const

type Props = Omit<ComponentProps<typeof Button>, 'variant' | 'size'> & {
  variant?: keyof typeof VARIANTS
  icon?: IconName
  block?: boolean
  loading?: boolean
  hideLabelOnMobile?: boolean
}

/**
 * Botón base: variantes primaria, secundaria, ghost y `danger` (confirmar una
 * acción destructiva); el texto envuelve dentro del botón si no cabe; ícono opcional,
 * spinner y `aria-busy` al cargar, foco visible y área táctil de 44px.
 * `hideLabelOnMobile` deja solo el ícono en mobile (el texto sigue siendo
 * el nombre accesible). Al pulsar se reduce a 0,98 con `motion-safe`, salvo
 * deshabilitado o en carga.
 *
 * @author Pablo Contreras
 * @since 2026/09/27
 * @since 2026/11/19
 */
export function UIButton({ variant = 'primary', icon, block = false, loading = false, hideLabelOnMobile = false, type = 'button', className, disabled, children, ...props }: Props): React.JSX.Element {
  const canPress = !disabled && !loading
  return (
    <Button
      type={type}
      variant={VARIANTS[variant]}
      disabled={disabled || loading}
      aria-busy={loading || undefined}
      className={cn(
        'ui-typography-body h-auto min-h-11 max-w-full gap-2 rounded-xl px-4 text-center font-bold whitespace-normal focus-visible:ui-focus',
        TONE[variant],
        block && 'w-full',
        hideLabelOnMobile && 'max-sm:w-11 max-sm:px-0',
        canPress && 'ui-press',
        className,
      )}
      {...props}
    >
      {loading ? <UIIcon name="loader" className="size-5 animate-spin motion-reduce:animate-none" /> : icon ? <UIIcon name={icon} /> : null}
      {hideLabelOnMobile ? <span className="max-sm:sr-only">{children}</span> : children}
    </Button>
  )
}

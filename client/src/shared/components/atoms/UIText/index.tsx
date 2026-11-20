import type { ReactNode } from 'react'

const VARIANTS = {
  display: { tag: 'p', className: 'ui-typography-display text-foreground' },
  title: { tag: 'h1', className: 'ui-typography-title-3 text-foreground' },
  subtitle: { tag: 'h2', className: 'ui-typography-subtitle-2 text-foreground' },
  heading: { tag: 'h3', className: 'ui-typography-body font-bold text-foreground' },
  body: { tag: 'p', className: 'ui-typography-body text-foreground-secondary' },
  caption: { tag: 'p', className: 'ui-typography-caption text-muted-foreground' },
  overline: { tag: 'p', className: 'ui-typography-overline text-accent-foreground' },
} as const

type Props = { variant?: keyof typeof VARIANTS; children: ReactNode; className?: string; id?: string }

/**
 * Texto tipográfico: la variante define el elemento semántico (h1-h3 o p)
 * y el estilo de la escala `ui-typography-*`. `id` sirve para asociar el texto con otro elemento
 * (p. ej. con `aria-describedby`).
 *
 * @author Pablo Contreras
 * @since 2026/09/27
 * @since 2026/11/19
 */
export function UIText({ variant = 'body', children, className = '', id }: Props): React.JSX.Element {
  const { tag: Tag, className: base } = VARIANTS[variant]
  return (
    <Tag id={id} className={`${base} ${className}`}>
      {children}
    </Tag>
  )
}

import type { ComponentProps } from 'react'

/**
 * Contenedor principal de una pantalla, centrado y con márgenes móviles.
 *
 * @author Pablo Contreras
 * @since 2026/09/27
 */
export function UIPage({ className = '', ...props }: ComponentProps<'main'>): React.JSX.Element {
  return <main className={`flex min-h-dvh items-center justify-center px-3 sm:px-4 py-10 motion-safe:animate-ui-enter ${className}`} {...props} />
}

import type { ComponentProps } from 'react'

/**
 * Formulario base: validación propia (i18n) en vez de la nativa del navegador. Sin `action` de función usa `POST`,
 * así un envío nativo antes de hidratar nunca pone los campos (claves incluidas) en la URL.
 *
 * @author Pablo Contreras
 * @since 2026/09/27
 */
export function UIForm({ className = '', ...props }: ComponentProps<'form'>): React.JSX.Element {
  const method = typeof props.action === 'function' ? undefined : 'post'
  return <form noValidate method={method} className={`flex flex-col gap-4 ${className}`} {...props} />
}

import { toast as sonner } from 'sonner'

import { Toaster } from '../../shadcn/sonner'

/**
 * Región de avisos no intrusivos (arriba al centro); `label` la nombra para
 * lectores de pantalla. Baja a 5rem en todo ancho para no tapar el header
 * sticky (h-16) y dura 6 s para leerlo. Se monta una sola vez en los providers.
 *
 * @author Pablo Contreras
 * @since 2026/09/27
 * @since 2026/11/19
 */
export function UIToaster({ label }: { label: string }): React.JSX.Element {
  return (
    <Toaster
      position="top-center"
      containerAriaLabel={label}
      richColors={false}
      duration={TOAST_MS}
      offset={{ top: '5rem' }}
      mobileOffset={{ top: '5rem' }}
    />
  )
}

const TOAST_MS = 6000

/** Avisos tipados: éxito o información (siempre con texto ya traducido). */
export const toast = {
  success: (message: string): void => {
    sonner.success(message)
  },
  info: (message: string): void => {
    sonner.info(message)
  },
}

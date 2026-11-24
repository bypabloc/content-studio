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

/** Un botón del aviso: `onClick` corre al pulsarlo (p. ej. «Abrir carpeta»). */
type ToastAction = { label: string; onClick: () => void }

/** `persistent`: queda hasta que se pulse su botón o se cierre (una actualización lista, spec 022). */
type ToastOptions = { action?: ToastAction; persistent?: boolean }

const sonnerOptions = ({ action, persistent }: ToastOptions) =>
  persistent ? { action, duration: Infinity, closeButton: true } : { action }

/**
 * Avisos tipados: éxito, error o información (siempre con texto ya traducido). Éxito y error pueden llevar un botón.
 * Sin opciones, sonner recibe solo el texto, como antes de los avisos tipados.
 */
export const toast = {
  success: (message: string, options?: ToastOptions): void => {
    if (options) sonner.success(message, sonnerOptions(options))
    else sonner.success(message)
  },
  error: (message: string, options?: ToastOptions): void => {
    if (options) sonner.error(message, sonnerOptions(options))
    else sonner.error(message)
  },
  info: (message: string, options?: ToastOptions): void => {
    if (options) sonner.info(message, sonnerOptions(options))
    else sonner.info(message)
  },
}

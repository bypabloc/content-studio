import type { ReactNode } from 'react'

/**
 * Texto corto cuyo valor completo va en su título nativo: el navegador lo muestra al pasar el cursor sin ocupar espacio en la tabla.
 *
 * @author Pablo Contreras
 * @since 2026/10/31
 *
 * @param props.full - Valor completo, sin cortar.
 * @param props.children - Texto corto que se muestra.
 * @returns Texto con su valor completo como título.
 */
export function UIDetailText({ full, children }: { full: string; children: ReactNode }): React.JSX.Element {
  return <span title={full}>{children}</span>
}

import type { ReactNode } from 'react'

/**
 * Estado en curso: anuncia `label` en una región viva (`<output>`, rol
 * status) oculta a la vista y muestra `children` como representación visual
 * (esqueletos, spinner).
 *
 * @author Pablo Contreras
 * @since 2026/09/27
 */
export function UIStatus({ label, children }: { label: string; children: ReactNode }): React.JSX.Element {
  return (
    <>
      <output className="sr-only">{label}</output>
      {children}
    </>
  )
}

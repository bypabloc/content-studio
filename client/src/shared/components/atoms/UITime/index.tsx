import type { ComponentProps } from 'react'

/**
 * Fecha con su valor de máquina (`dateTime`, ISO) y su texto legible: el `<time>` nativo. Solo los átomos usan
 * etiquetas nativas (spec 008, D-4); las moléculas que muestran una fecha la reciben de aquí.
 */
export function UITime({ dateTime, className, children, ...props }: ComponentProps<'time'>): React.JSX.Element {
  return (
    <time dateTime={dateTime} className={className} {...props}>
      {children}
    </time>
  )
}

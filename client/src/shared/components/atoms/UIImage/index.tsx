import type { ComponentProps } from 'react'

type Props = Omit<ComponentProps<'img'>, 'alt'> & { alt: string }

/**
 * Imagen con su texto alternativo obligatorio. Las moléculas la usan en vez de un `img` suelto (spec 008, D-4); el
 * tamaño lo fija quien la usa, con `width` y `height` para evitar saltos de layout.
 */
export function UIImage({ alt, className, ...props }: Props): React.JSX.Element {
  return <img alt={alt} className={className} {...props} />
}

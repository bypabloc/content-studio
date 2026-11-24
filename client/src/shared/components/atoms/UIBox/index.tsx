import type { ComponentProps } from 'react';

const TAGS = ['div', 'span', 'section', 'header', 'nav', 'aside', 'main', 'footer'] as const;

type Props = Omit<ComponentProps<'div'>, 'as'> & { as?: (typeof TAGS)[number] };

/**
 * Contenedor genérico: `as` elige la etiqueta y el resto de atributos llegan al elemento. Lo usan las moléculas y los
 * organismos en vez de un `div` suelto (spec 008, D-4); las pantallas arman su layout con `UIStack`, `UIGrid` y `UICard`.
 */
export function UIBox({ as = 'div', className, ...props }: Props): React.JSX.Element {
  const Tag = as;
  return <Tag className={className} {...props} />;
}

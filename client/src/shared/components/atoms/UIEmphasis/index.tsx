import type { ReactNode } from 'react';

/**
 * Énfasis dentro de un texto: negrita sin cambiar el tamaño ni el color del texto que lo rodea. Es un átomo porque el
 * `strong` nativo no va fuera de los átomos (la etapa ui-structure).
 */
export function UIEmphasis({ children }: { children: ReactNode }): React.JSX.Element {
  return <strong className="font-semibold">{children}</strong>;
}

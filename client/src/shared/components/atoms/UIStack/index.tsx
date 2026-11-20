import type { ComponentProps } from 'react'

const GAPS = { xs: 'gap-1', sm: 'gap-2', md: 'gap-4', lg: 'gap-6', xl: 'gap-10' } as const;
const DIRECTIONS = { column: 'flex-col', row: 'flex-row' } as const;
const ALIGN = { start: 'items-start', center: 'items-center', end: 'items-end', stretch: 'items-stretch' } as const;
const JUSTIFY = {
  start: 'justify-start',
  center: 'justify-center',
  end: 'justify-end',
  between: 'justify-between',
} as const;

type Props = ComponentProps<'div'> & {
  gap?: keyof typeof GAPS;
  direction?: keyof typeof DIRECTIONS;
  align?: keyof typeof ALIGN;
  justify?: keyof typeof JUSTIFY;
};

/**
 * Apila su contenido en columna (por defecto) o en fila, con un espaciado de la
 * escala y, si se pide, la alineación de los ejes.
 *
 * @author Pablo Contreras
 * @since 2026/09/27
 * @since 2026/11/19
 */
export function UIStack({ gap = 'md', direction = 'column', align, justify, className = '', ...props }: Props): React.JSX.Element {
  const classes = ['flex', DIRECTIONS[direction], GAPS[gap], align && ALIGN[align], justify && JUSTIFY[justify], className];
  return <div className={classes.filter(Boolean).join(' ')} {...props} />;
}

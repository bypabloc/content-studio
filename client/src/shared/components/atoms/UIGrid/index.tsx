import type { ComponentProps } from 'react'

const COLUMNS = { 2: 'grid-cols-1 gap-4 sm:grid-cols-2', 3: 'grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3', 4: 'grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4', compact: 'grid-cols-3 gap-2 sm:grid-cols-4' } as const

type Props = ComponentProps<'div'> & { columns?: keyof typeof COLUMNS }

/**
 * Grilla responsive mobile-first: una columna en mobile y hasta `columns`
 * desde tablet/desktop; `compact` es para chips cortos (horarios): 3 columnas
 * en mobile y 4 desde tablet.
 *
 * @author Pablo Contreras
 * @since 2026/09/27
 */
export function UIGrid({ columns = 3, className = '', ...props }: Props): React.JSX.Element {
  return <div className={`grid ${COLUMNS[columns]} ${className}`} {...props} />
}

import type { ComponentProps } from 'react'

import { UIField } from '../UIField'

type Props = Omit<ComponentProps<typeof UIField>, 'onChange' | 'type' | 'icon'> & { onChange: (value: string) => void }

/**
 * Campo de búsqueda (`type="search"`) con ícono de lupa y label visible.
 *
 * @author Pablo Contreras
 * @since 2026/09/27
 * @since 2026/11/19
 */
export function UISearchField({ onChange, ...props }: Props): React.JSX.Element {
  return <UIField type="search" icon="search" onChange={(e) => onChange(e.target.value)} {...props} />
}

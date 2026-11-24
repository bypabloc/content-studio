import type { ReactNode } from 'react'

import { Empty, EmptyContent, EmptyDescription, EmptyHeader, EmptyMedia } from '../../shadcn/empty'

import { type IconName, UIIcon } from '../../atoms/UIIcon'

type Props = { icon: IconName; title: string; description?: string; action?: ReactNode; level?: 1 | 2 | 3 | 4 }

/**
 * Estado vacío (o sin permiso): ícono decorativo, título (`h2` por defecto;
 * `level` lo ajusta dentro de una tarjeta), descripción y acción opcional.
 *
 * @author Pablo Contreras
 * @since 2026/09/27
 * @since 2026/11/19
 */
export function UIEmpty({ icon, title, description, action, level = 2 }: Props): React.JSX.Element {
  const Heading = `h${level}` as const
  return (
    <Empty className="gap-5 px-6 py-12">
      <EmptyHeader className="gap-3">
        <EmptyMedia variant="icon" className="size-12 rounded-2xl bg-accent text-accent-foreground">
          <UIIcon name={icon} className="size-6" />
        </EmptyMedia>
        <Heading className="ui-typography-subtitle-2 text-foreground">{title}</Heading>
        {description ? <EmptyDescription className="ui-typography-body text-foreground-secondary">{description}</EmptyDescription> : null}
      </EmptyHeader>
      {action ? <EmptyContent>{action}</EmptyContent> : null}
    </Empty>
  )
}

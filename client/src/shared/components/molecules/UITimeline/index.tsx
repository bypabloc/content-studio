import type { ReactNode } from 'react'
import { UIBox } from '../../atoms/UIBox'

/** Entrada de `UITimeline`: `dateTime` ISO para `<time>` y `date` ya formateada. */
export type UITimelineItem = { key: string | number; dateTime: string; date: string; children: ReactNode }

/**
 * Línea de tiempo accesible: lista ordenada (`ol`) con nombre, un punto de
 * marca por entrada y la fecha como `<time>`. Respeta el orden recibido
 * (el historial llega del más reciente al más antiguo).
 *
 * @author Pablo Contreras
 * @since 2026/09/28
 * @since 2026/11/19
 */
export function UITimeline({ label, items }: { label: string; items: UITimelineItem[] }): React.JSX.Element {
  return (
    <UIBox role="list" aria-label={label} className="flex flex-col">
      {items.map(({ key, dateTime, date, children }) => (
        <UIBox role="listitem" key={key} className="motion-safe:animate-ui-enter relative flex flex-col gap-2 border-l-2 border-border pb-6 pl-6 last:pb-0">
          <UIBox as="span" aria-hidden="true" className="absolute top-1 -left-[7px] size-3 rounded-full bg-primary ring-4 ring-background" />
          <time dateTime={dateTime} className="ui-typography-caption font-bold text-foreground-secondary">
            {date}
          </time>
          {children}
        </UIBox>
      ))}
    </UIBox>
  )
}

import type { ReactNode } from 'react'

import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../shadcn/tabs'
import { UIBox } from '../../atoms/UIBox'

type Props = {
  value: string
  onValueChange: (value: string) => void
  label: string
  items: { value: string; label: string }[]
  analyticsId?: 'account.tab' | 'appointments.view' | 'patients.record_tab' | 'patients.trends_range' | 'reports.tab' | 'settings.tab'
  children: ReactNode
}

/**
 * Pestañas controladas: lista etiquetada (`aria-label`) con pestañas de 44px
 * que en mobile envuelven en filas (todas visibles, sin scroll oculto) y en
 * desktop se desplazan en horizontal si no caben, y un único
 * panel con el contenido de la pestaña activa.
 *
 * @author Pablo Contreras
 * @since 2026/09/28
 * @since 2026/11/19
 */
export function UITabs({ value, onValueChange, label, items, analyticsId, children }: Props): React.JSX.Element {
  return (
    <Tabs value={value} onValueChange={(next) => onValueChange(String(next))} className="w-full min-w-0 gap-4">
      <UIBox className="w-full overflow-x-auto">
        <TabsList aria-label={label} className="min-w-max gap-1 rounded-xl p-1 group-data-horizontal/tabs:h-auto max-sm:w-full max-sm:min-w-0 max-sm:flex-wrap max-sm:justify-start">
          {items.map((item) => {
            const id = item.value
            return (
              <TabsTrigger
                key={item.value}
                value={item.value}
                className="ui-typography-body h-auto min-h-11 flex-none cursor-pointer rounded-lg px-4 font-bold text-foreground-secondary focus-visible:ui-focus data-active:bg-card data-active:text-foreground data-active:shadow-ui dark:text-foreground-secondary dark:data-active:bg-card"
                data-analytics={analyticsId}
                data-analytics-detail={id}
              >
                {item.label}
              </TabsTrigger>
            )
          })}
        </TabsList>
      </UIBox>
      <TabsContent key={value} value={value} className="ui-typography-body min-w-0 text-foreground motion-safe:animate-ui-fade">
        {children}
      </TabsContent>
    </Tabs>
  )
}

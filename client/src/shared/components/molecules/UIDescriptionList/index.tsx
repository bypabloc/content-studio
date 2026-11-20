import { type IconName, UIIcon } from '../../atoms/UIIcon'
import { UIBox } from '../../atoms/UIBox'

type Item = { icon: IconName; term: string; detail: string | readonly string[] }

function wrapClass(detail: string | readonly string[]): string {
  if (typeof detail !== 'string') return 'wrap-break-word space-y-1.5'
  return /\s/.test(detail) ? 'wrap-break-word' : 'wrap-anywhere'
}

/**
 * Lista de pares término-detalle con ícono: 1, 2 o 3 columnas según el ancho del
 * contenedor. Los valores largos se parten en vez de truncarse. Sin `dl`
 * nativa (spec 008, D-4): el grupo es una lista (`role="list"`) y cada par, un
 * ítem con su término y su detalle.
 *
 * @author Pablo Contreras
 * @since 2026/09/27
 * @since 2026/11/19
 */
export function UIDescriptionList({ items }: { items: Item[] }): React.JSX.Element {
  return (
    <UIBox className="@container">
      <UIBox role="list" className="grid grid-cols-1 gap-4 @lg:grid-cols-2 @3xl:grid-cols-3">
        {items.map(({ icon, term, detail }) => (
          <UIBox role="listitem" key={term} className="flex min-w-0 flex-col gap-2 rounded-xl bg-muted p-4">
            <UIBox className="flex items-center gap-2 ui-typography-caption text-muted-foreground">
              <UIBox as="span" aria-hidden="true" className="grid size-8 shrink-0 place-items-center rounded-lg bg-card text-accent-foreground shadow-ui">
                <UIIcon name={icon} />
              </UIBox>
              {term}
            </UIBox>
            <UIBox className={`ui-typography-body font-bold text-pretty text-foreground ${wrapClass(detail)}`}>
              {typeof detail === 'string'
                ? detail
                : detail.map((line, index) => (
                    <UIBox as="span" key={index} className="block">
                      {line}
                    </UIBox>
                  ))}
            </UIBox>
          </UIBox>
        ))}
      </UIBox>
    </UIBox>
  )
}

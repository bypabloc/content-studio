import { UIButton } from '../../atoms/UIButton'
import { UIBox } from '../../atoms/UIBox'
import { UIText } from '../../atoms/UIText'

type Props = {
  total: number
  limit: number
  offset: number
  onChange: (offset: number) => void
  summary: string
  labels: { nav: string; previous: string; next: string }
}

/**
 * Paginación limit/offset: resumen con el total real ("Mostrando 1–20 de
 * N") y botones Anterior/Siguiente deshabilitados en los extremos.
 *
 * @author Pablo Contreras
 * @since 2026/09/27
 * @since 2026/11/19
 */
export function UIPagination({ total, limit, offset, onChange, summary, labels }: Props): React.JSX.Element {
  return (
    <UIBox as="nav" aria-label={labels.nav} className="flex flex-wrap items-center justify-between gap-3">
      <UIText className="ui-typography-caption text-foreground-secondary tabular-nums">{summary}</UIText>
      {/* Con una sola página los botones no llevan a ningún lado: solo queda el resumen. */}
      {total <= limit && offset === 0 ? null : (
      <UIBox className="flex gap-2">
        <UIButton variant="secondary" icon="chevron-left" hideLabelOnMobile disabled={offset === 0} onClick={() => onChange(Math.max(0, offset - limit))}>
          {labels.previous}
        </UIButton>
        <UIButton variant="secondary" icon="chevron-right" hideLabelOnMobile disabled={offset + limit >= total} onClick={() => onChange(offset + limit)}>
          {labels.next}
        </UIButton>
      </UIBox>
      )}
    </UIBox>
  )
}

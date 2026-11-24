import type { ReactNode } from 'react'

import { UIBox } from '../../atoms/UIBox'
import { UIButton } from '../../atoms/UIButton'
import { UICard } from '../../atoms/UICard'
import { UIText } from '../../atoms/UIText'

type Row = { _row: string }
type Props<T extends Row> = {
  label: string
  items: T[]
  min: number
  max: number
  addLabel: string
  removeLabel: string
  missingLabel: (missing: number) => string
  createItem: () => T
  onChange: (items: T[]) => void
  renderItem: (item: T, index: number) => ReactNode
}

/**
 * Grupo «agregar otro»: cada elemento lleva su `_row` estable y se quita sin
 * tocar a los demás. El contador indica cuántos faltan para el mínimo y el
 * botón de agregar se deshabilita al llegar al máximo. Es controlado: el
 * padre guarda los elementos.
 *
 * @author Pablo Contreras
 * @since 2026/11/10
 */
export function UIRepeatGroup<T extends Row>({
  label,
  items,
  min,
  max,
  addLabel,
  removeLabel,
  missingLabel,
  createItem,
  onChange,
  renderItem,
}: Props<T>): React.JSX.Element {
  const missing = min - items.length

  return (
    <UIBox as="section" className="flex flex-col gap-3">
      <UIText variant="heading">{label}</UIText>
      {items.map((item, index) => (
        <UICard key={item._row} className="gap-2 p-3 sm:p-3">
          {renderItem(item, index)}
          <UIButton variant="secondary" icon="trash-2" onClick={() => onChange(items.filter((other) => other._row !== item._row))}>
            {removeLabel}
          </UIButton>
        </UICard>
      ))}
      {missing > 0 ? <UIText variant="caption">{missingLabel(missing)}</UIText> : null}
      <UIButton variant="secondary" disabled={items.length >= max} onClick={() => onChange([...items, createItem()])}>
        {addLabel}
      </UIButton>
    </UIBox>
  )
}

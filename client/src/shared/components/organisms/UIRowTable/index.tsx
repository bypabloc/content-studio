import type { ReactNode } from 'react'

import { Table, TableBody, TableCaption, TableCell, TableHead, TableHeader, TableRow } from '../../shadcn/table'
import { UIButton } from '../../atoms/UIButton'
import { CARD_SURFACE } from '../../atoms/UICard'
import { UIText } from '../../atoms/UIText'
import { UIBox } from '../../atoms/UIBox'

type Row = { _row: string }
type Props<T extends Row> = {
  caption: string
  columns: string[]
  items: T[]
  min: number
  max: number
  addLabel: string
  removeLabel: string
  missingLabel: (missing: number) => string
  createItem: () => T
  onChange: (items: T[]) => void
  renderCells: (item: T, index: number) => ReactNode[]
}

/** Móvil: cada fila es una ficha con la superficie de `UICard` y cada campo muestra su columna encima; desde `@3xl` vuelve a ser una fila de tabla, porque antes los campos editables se cortan. */
const CARD_ROW = `${CARD_SURFACE} border-input hover:bg-card @3xl:hover:bg-transparent flex flex-col gap-2 p-3 border-b-0 @3xl:table-row @3xl:rounded-none @3xl:bg-transparent @3xl:p-0 @3xl:border-b @3xl:shadow-none @3xl:ring-0`
const FIELD_CELL =
  'block whitespace-normal p-0 before:mb-1 before:block before:font-bold before:text-foreground-secondary before:ui-typography-caption before:content-[attr(data-label)] @3xl:table-cell @3xl:p-2 @3xl:before:content-none'
const ACTION_CELL = 'block whitespace-normal p-0 text-right @3xl:table-cell @3xl:p-2'

/**
 * Tabla de N filas sobre `shadcn/table`, dentro de una región con nombre y
 * enfocable: cada fila es un `_row` estable que se quita sin tocar a las
 * demás. El padre devuelve el contenido de cada celda como lista y esta tabla
 * lo envuelve en su celda; el contador y el límite de filas funcionan como en
 * `UIRepeatGroup`. Con poco ancho (`@container`) cada fila se muestra como
 * ficha y la cabecera queda solo para lectores de pantalla.
 *
 * @author Pablo Contreras
 * @since 2026/11/10
 */
export function UIRowTable<T extends Row>({
  caption,
  columns,
  items,
  min,
  max,
  addLabel,
  removeLabel,
  missingLabel,
  createItem,
  onChange,
  renderCells,
}: Props<T>): React.JSX.Element {
  const missing = min - items.length

  return (
    <UIBox className="@container flex flex-col gap-3">
      <Table containerLabel={caption} className="block @3xl:table">
        <TableCaption className="block caption-top mb-2 mt-0 text-left font-bold text-foreground-secondary ui-typography-caption @3xl:table-caption">
          {caption}
        </TableCaption>
        <TableHeader className="sr-only @3xl:not-sr-only">
          <TableRow className="hover:bg-transparent">
            {columns.map((column) => (
              <TableHead
                key={column}
                scope="col"
                className="h-auto px-2 pb-2 text-left font-bold text-foreground-secondary ui-typography-caption"
              >
                {column}
              </TableHead>
            ))}
            <TableHead scope="col" className="h-auto">
              <UIBox as="span" className="sr-only">{removeLabel}</UIBox>
            </TableHead>
          </TableRow>
        </TableHeader>
        <TableBody className="flex flex-col gap-3 @3xl:table-row-group">
          {items.map((item, index) => (
            <TableRow key={item._row} className={CARD_ROW}>
              {renderCells(item, index).map((cell, column) => (
                <TableCell key={column} data-label={columns[column]} className={FIELD_CELL}>
                  {cell}
                </TableCell>
              ))}
              <TableCell className={ACTION_CELL}>
                <UIButton variant="secondary" icon="trash-2" onClick={() => onChange(items.filter((other) => other._row !== item._row))}>
                  {removeLabel}
                </UIButton>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
      {missing > 0 ? <UIText variant="caption">{missingLabel(missing)}</UIText> : null}
      <UIButton variant="secondary" disabled={items.length >= max} onClick={() => onChange([...items, createItem()])}>
        {addLabel}
      </UIButton>
    </UIBox>
  )
}

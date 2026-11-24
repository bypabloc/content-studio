import { cn } from 'cn'
import type { ReactNode } from 'react'

import { Skeleton } from '../../shadcn/skeleton'
import { Table, TableBody, TableCaption, TableCell, TableHead, TableHeader, TableRow } from '../../shadcn/table'
import { UIBox } from '../../atoms/UIBox'

/**
 * Columna de `UITable`: `end` alinea a la derecha con cifras tabulares; `wide`
 * marca un texto largo, que al apilarse va debajo de su etiqueta y al inicio.
 */
export type UITableColumn<T> = { key: string; header: string; align?: 'start' | 'end'; wide?: boolean; render: (row: T) => ReactNode }

type Props<T> = {
  caption: string
  columns: UITableColumn<T>[]
  rows: T[]
  rowKey: (row: T) => string | number
  stackAt?: '2xl' | '5xl'
  loading?: boolean
  loadingRows?: number
  empty?: ReactNode
}

const align = (value: UITableColumn<unknown>['align']): string => (value === 'end' ? 'text-right tabular-nums' : 'text-left')

// Bajo 42 rem de contenedor la tabla se apila: cada fila es una tarjeta y cada celda muestra su encabezado.
// La etiqueta usa texto alternativo vacío (`content: attr() / ''`): los lectores ya oyen el encabezado de la columna.
const STACK_TABLE = '@max-2xl/table:block'
const STACK_ROW = '@max-2xl/table:grid @max-2xl/table:gap-1 @max-2xl/table:py-3'
const STACK_CELL = [
  '@max-2xl/table:flex @max-2xl/table:min-h-0 @max-2xl/table:flex-wrap @max-2xl/table:items-center @max-2xl/table:justify-between',
  '@max-2xl/table:gap-x-4 @max-2xl/table:gap-y-1 @max-2xl/table:py-1 @max-2xl/table:text-right @max-2xl/table:[&>*]:ml-auto',
  '@max-2xl/table:[&>*]:max-w-full @max-2xl/table:[&>*]:min-w-0 @max-2xl/table:before:shrink-0 @max-2xl/table:before:text-left',
  '@max-2xl/table:before:font-bold @max-2xl/table:before:text-foreground-secondary @max-2xl/table:before:content-[attr(data-label)_/_""]',
].join(' ')
const STACK_FULL = '@max-2xl/table:block'
// La primera columna es el título de la tarjeta: sin etiqueta y alineada al inicio.
const STACK_TITLE = '@max-2xl/table:justify-start @max-2xl/table:text-left @max-2xl/table:font-bold @max-2xl/table:before:content-none @max-2xl/table:[&>*]:ml-0'
// Un texto largo apilado va debajo de su etiqueta y al inicio, no a la derecha.
const STACK_WIDE = '@max-2xl/table:block @max-2xl/table:text-left @max-2xl/table:before:block @max-2xl/table:[&>*]:ml-0'

const STACK_TABLE_5XL = '@max-5xl/table:block'
const STACK_ROW_5XL = '@max-5xl/table:grid @max-5xl/table:gap-1 @max-5xl/table:py-3'
const STACK_CELL_5XL = [
  '@max-5xl/table:flex @max-5xl/table:min-h-0 @max-5xl/table:flex-wrap @max-5xl/table:items-center @max-5xl/table:justify-between',
  '@max-5xl/table:gap-x-4 @max-5xl/table:gap-y-1 @max-5xl/table:py-1 @max-5xl/table:text-right @max-5xl/table:[&>*]:ml-auto',
  '@max-5xl/table:[&>*]:max-w-full @max-5xl/table:[&>*]:min-w-0 @max-5xl/table:before:shrink-0 @max-5xl/table:before:text-left',
  '@max-5xl/table:before:font-bold @max-5xl/table:before:text-foreground-secondary @max-5xl/table:before:content-[attr(data-label)_/_""]',
].join(' ')
const STACK_FULL_5XL = '@max-5xl/table:block'
const STACK_TITLE_5XL = '@max-5xl/table:justify-start @max-5xl/table:text-left @max-5xl/table:font-bold @max-5xl/table:before:content-none @max-5xl/table:[&>*]:ml-0'
const STACK_WIDE_5XL = '@max-5xl/table:block @max-5xl/table:text-left @max-5xl/table:before:block @max-5xl/table:[&>*]:ml-0'

/**
 * Tabla de datos: leyenda solo para lectores de pantalla, números a la
 * derecha con `tabular-nums`, valores largos partidos solo si una palabra no
 * cabe (nunca truncados), filas apiladas como tarjetas con la etiqueta de su
 * columna bajo el breakpoint configurado, roles explícitos,
 * filas de esqueleto que reservan el espacio al cargar y un nodo de vacío.
 *
 * @author Pablo Contreras
 * @since 2026/09/27
 */
export function UITable<T>({ caption, columns, rows, rowKey, stackAt = '2xl', loading = false, loadingRows = 5, empty }: Props<T>): React.JSX.Element {
  const stackTable = stackAt === '5xl' ? STACK_TABLE_5XL : STACK_TABLE
  const stackRow = stackAt === '5xl' ? STACK_ROW_5XL : STACK_ROW
  const stackCell = stackAt === '5xl' ? STACK_CELL_5XL : STACK_CELL
  const stackFull = stackAt === '5xl' ? STACK_FULL_5XL : STACK_FULL
  const stackTitle = stackAt === '5xl' ? STACK_TITLE_5XL : STACK_TITLE
  const stackWide = stackAt === '5xl' ? STACK_WIDE_5XL : STACK_WIDE
  const stackHeader = stackAt === '5xl' ? '@max-5xl/table:sr-only' : '@max-2xl/table:sr-only'
  const stackSkeleton = stackAt === '5xl' ? '@max-5xl/table:h-auto' : '@max-2xl/table:h-auto'

  return (
    <UIBox className="@container/table overflow-hidden rounded-2xl border border-border bg-card shadow-ui">
      <Table containerLabel={caption} role="table" aria-busy={loading || undefined} className={cn('ui-typography-body text-foreground', stackTable)}>
        <TableCaption className="sr-only">{caption}</TableCaption>
        <TableHeader className={cn('bg-muted', stackHeader)}>
          <TableRow role="row" className="hover:bg-muted">
            {columns.map((c) => (
              <TableHead key={c.key} role="columnheader" scope="col" className={cn('ui-typography-caption h-11 px-4 font-bold text-foreground-secondary', align(c.align))}>
                {c.header}
              </TableHead>
            ))}
          </TableRow>
        </TableHeader>
        <TableBody className={stackTable}>
          {loading
            ? Array.from({ length: loadingRows }, (_, i) => (
                <TableRow key={`loading-${i}`} role="row" className={stackRow}>
                  {columns.map((c) => (
                    <TableCell key={c.key} role="cell" className={cn('h-14 px-4', stackFull, stackSkeleton)}>
                      <Skeleton className="h-4 w-full max-w-40" />
                    </TableCell>
                  ))}
                </TableRow>
              ))
            : null}
          {!loading && rows.length === 0 && empty ? (
            <TableRow role="row" className={cn('hover:bg-transparent', stackFull)}>
              <TableCell role="cell" colSpan={columns.length} className={cn('p-6 text-center whitespace-normal', stackFull)}>
                {empty}
              </TableCell>
            </TableRow>
          ) : null}
          {loading
            ? null
            : rows.map((row) => (
                <TableRow key={rowKey(row)} role="row" className={cn('motion-safe:animate-ui-fade', stackRow)}>
                  {columns.map((c, index) => (
                    <TableCell key={c.key} role="cell" data-label={c.header} className={cn('min-h-14 px-4 py-3 whitespace-normal wrap-break-word', align(c.align), stackCell, index === 0 && stackTitle, c.wide && stackWide)}>
                      {c.render(row)}
                    </TableCell>
                  ))}
                </TableRow>
              ))}
        </TableBody>
      </Table>
    </UIBox>
  )
}

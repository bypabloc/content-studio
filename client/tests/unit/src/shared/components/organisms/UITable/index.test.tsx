import { render, screen, within } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { UITable, type UITableColumn } from '@/shared/components/organisms/UITable'

type Row = { id: number; name: string; total: number }
const COLUMNS: UITableColumn<Row>[] = [
  { key: 'name', header: 'Nombre', render: (f) => f.name },
  { key: 'total', header: 'Total', align: 'end', render: (f) => f.total },
]
const ROWS: Row[] = [
  { id: 1, name: 'Ana', total: 10 },
  { id: 2, name: 'Luis', total: 200 },
]
const NEXT_PAGE: Row[] = [
  { id: 3, name: 'Marta', total: 30 },
  { id: 4, name: 'Pablo', total: 40 },
]
const FADE_CLASS = 'motion-safe:animate-ui-fade'
const dataRows = (): HTMLTableRowElement[] => Array.from(screen.getByRole('table', { name: 'Usuarios' }).querySelectorAll('tbody tr'))

describe('UITable [AC-9]', () => {
  it('WHEN there are rows THEN table with accessible caption, headers and right-aligned numbers', () => {
    render(<UITable caption="Usuarios" columns={COLUMNS} rows={ROWS} rowKey={(f) => f.id} />)

    const table = screen.getByRole('table', { name: 'Usuarios' })
    expect(within(table).getAllByRole('row')).toHaveLength(3)
    expect(screen.getByRole('region', { name: 'Usuarios' }).getAttribute('tabindex')).toBe('0')
    const total = screen.getByRole('cell', { name: '200' })
    expect(total.className).toContain('text-right')
    expect(total.className).toContain('tabular-nums')
    expect(screen.getByRole('columnheader', { name: 'Total' }).className).toContain('text-right')
    expect(screen.getByRole('cell', { name: 'Ana' }).className).toContain('wrap-break-word')
  })

  it('WHEN cells render THEN they break only words that do not fit, never anywhere [AC-1.2]', () => {
    render(<UITable caption="Usuarios" columns={COLUMNS} rows={ROWS} rowKey={(f) => f.id} />)

    const table = screen.getByRole('table', { name: 'Usuarios' })
    expect(table.outerHTML).not.toContain(['wrap', 'anywhere'].join('-'))
  })

  it('WHEN the table renders THEN every cell carries its column header as data-label [AC-1.1]', () => {
    render(<UITable caption="Usuarios" columns={COLUMNS} rows={ROWS} rowKey={(f) => f.id} />)

    expect(screen.getByRole('cell', { name: 'Ana' }).getAttribute('data-label')).toBe('Nombre')
    expect(screen.getByRole('cell', { name: '200' }).getAttribute('data-label')).toBe('Total')
  })

  it('WHEN the container is narrow THEN rows stack as cards with the label before each value [AC-1.1]', () => {
    render(<UITable caption="Usuarios" columns={COLUMNS} rows={ROWS} rowKey={(f) => f.id} />)

    const row = screen.getByRole('cell', { name: 'Ana' }).closest('tr')
    expect(row?.className).toContain('@max-2xl/table:grid')
    const cell = screen.getByRole('cell', { name: '200' })
    expect(cell.className).toContain('@max-2xl/table:before:content-[attr(data-label)')
    expect(screen.getByRole('cell', { name: 'Ana' }).className).toContain('@max-2xl/table:before:content-none')
    expect(screen.getByRole('table', { name: 'Usuarios' }).querySelector('thead')?.className).toContain('@max-2xl/table:sr-only')
  })

  it('WHEN stackAt is 5xl THEN rows stack at the wider container breakpoint', () => {
    render(<UITable caption="Usuarios" columns={COLUMNS} rows={ROWS} rowKey={(f) => f.id} stackAt="5xl" />)

    const table = screen.getByRole('table', { name: 'Usuarios' })
    const row = screen.getByRole('cell', { name: 'Ana' }).closest('tr')
    const cell = screen.getByRole('cell', { name: '200' })
    expect(table.className).toContain('@max-5xl/table:block')
    expect(row?.className).toContain('@max-5xl/table:grid')
    expect(cell.className).toContain('@max-5xl/table:before:content-[attr(data-label)')
    expect(table.querySelector('thead')?.className).toContain('@max-5xl/table:sr-only')
  })

  it('WHEN a column is wide THEN its stacked value goes under the label and at the start', () => {
    const columns: UITableColumn<Row>[] = [COLUMNS[0]!, { key: 'notes', header: 'Notes', wide: true, render: (f) => `Note about ${f.name}` }]
    render(<UITable caption="Usuarios" columns={columns} rows={ROWS} rowKey={(f) => f.id} />)

    const cell = screen.getByRole('cell', { name: 'Note about Ana' })
    expect(cell.className).toContain('@max-2xl/table:before:content-[attr(data-label)')
    expect(cell.className).toContain('@max-2xl/table:before:block')
    expect(screen.getByRole('cell', { name: 'Ana' }).className).not.toContain('@max-2xl/table:text-left @max-2xl/table:before:block')
  })

  it('WHEN rendered THEN table, rows, headers and cells declare their roles explicitly [AC-1.3]', () => {
    render(<UITable caption="Usuarios" columns={COLUMNS} rows={ROWS} rowKey={(f) => f.id} />)

    const table = screen.getByRole('table', { name: 'Usuarios' })
    expect(table.getAttribute('role')).toBe('table')
    expect(table.querySelector('tbody tr')?.getAttribute('role')).toBe('row')
    expect(table.querySelector('th')?.getAttribute('role')).toBe('columnheader')
    expect(table.querySelector('td')?.getAttribute('role')).toBe('cell')
  })

  it('WHEN loading THEN rows reserved with skeletons and busy table', () => {
    render(<UITable caption="Usuarios" columns={COLUMNS} rows={[]} rowKey={(f) => f.id} loading loadingRows={3} />)

    const table = screen.getByRole('table', { name: 'Usuarios' })
    expect(table.getAttribute('aria-busy')).toBe('true')
    expect(within(table).getAllByRole('row')).toHaveLength(4)
    expect(table.querySelectorAll('[data-slot="skeleton"]')).toHaveLength(6)
  })

  it('WHEN there are no rows THEN shows the empty state spanning all columns', () => {
    render(<UITable caption="Usuarios" columns={COLUMNS} rows={[]} rowKey={(f) => f.id} empty={<p>No users</p>} />)

    const cell = screen.getByText('No users').closest('td')
    expect(cell?.getAttribute('colspan')).toBe('2')
    expect(cell?.className).toContain('p-6')
    expect(cell?.className).toContain('text-center')
  })

  it('WHEN data rows render THEN each row has the fade class [AC-9]', () => {
    render(<UITable caption="Usuarios" columns={COLUMNS} rows={ROWS} rowKey={(f) => f.id} />)

    expect(dataRows().map((row) => row.className.includes(FADE_CLASS))).toEqual([true, true])
  })

  it('WHEN the table is loading THEN the skeleton rows have no fade class [AC-9]', () => {
    render(<UITable caption="Usuarios" columns={COLUMNS} rows={[]} rowKey={(f) => f.id} loading loadingRows={2} />)

    expect(dataRows().map((row) => row.className.includes(FADE_CLASS))).toEqual([false, false])
  })

  it('WHEN the rows change to another page THEN the new rows are new nodes with the fade class [AC-9]', () => {
    const { rerender } = render(<UITable caption="Usuarios" columns={COLUMNS} rows={ROWS} rowKey={(f) => f.id} />)
    const previous = dataRows()

    rerender(<UITable caption="Usuarios" columns={COLUMNS} rows={NEXT_PAGE} rowKey={(f) => f.id} />)

    const current = dataRows()
    expect(current.map((row) => previous.includes(row))).toEqual([false, false])
    expect(current.map((row) => row.className.includes(FADE_CLASS))).toEqual([true, true])
  })
})

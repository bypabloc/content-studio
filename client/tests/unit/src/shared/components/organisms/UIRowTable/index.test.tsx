import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { CARD_SURFACE } from '@/shared/components/atoms/UICard'
import { UIRowTable } from '@/shared/components/organisms/UIRowTable'

type Row = { _row: string; name: string }

const ITEMS: Row[] = [
  { _row: 'a', name: 'Ana' },
  { _row: 'b', name: 'Beto' },
  { _row: 'c', name: 'Carla' },
]

const props = {
  caption: 'Hijos',
  columns: ['Nombre'],
  addLabel: 'Agregar otro',
  removeLabel: 'Quitar',
  missingLabel: (missing: number) => `Faltan ${missing}`,
  createItem: (): Row => ({ _row: 'new', name: '' }),
  renderCells: (item: Row) => [item.name],
}

describe('UIRowTable [AC-4]', () => {
  it('WHEN rendered THEN a table with its caption has one row per item plus the header [AC-4]', () => {
    render(<UIRowTable {...props} items={ITEMS} min={1} max={5} onChange={vi.fn()} />)

    const table = screen.getByRole('table', { name: 'Hijos' })

    expect(within(table).getAllByRole('row')).toHaveLength(ITEMS.length + 1)
    expect(within(table).getByRole('cell', { name: 'Beto' })).toBeTruthy()
  })

  it('WHEN the rows render as cards THEN the body spaces them apart [H4]', () => {
    const { container } = render(<UIRowTable {...props} items={ITEMS} min={1} max={5} onChange={vi.fn()} />)

    expect(container.querySelector('tbody')?.className).toContain('gap-3')
  })

  it('WHEN rendered THEN the table sits in a named, keyboard-reachable region [AC-4]', () => {
    render(<UIRowTable {...props} items={ITEMS} min={1} max={5} onChange={vi.fn()} />)

    const region = screen.getByRole('region', { name: 'Hijos' })

    expect(within(region).getByRole('table', { name: 'Hijos' })).toBeTruthy()
    expect(region.getAttribute('tabindex')).toBe('0')
  })

  it('WHEN a row is added THEN the row from createItem is appended [AC-4]', async () => {
    const user = userEvent.setup()
    const onChange = vi.fn()
    render(<UIRowTable {...props} items={ITEMS.slice(0, 1)} min={1} max={3} onChange={onChange} />)

    await user.click(screen.getByRole('button', { name: 'Agregar otro' }))

    expect(onChange).toHaveBeenCalledWith([ITEMS[0], { _row: 'new', name: '' }])
  })

  it('WHEN a middle row is removed THEN the other rows keep their _row and values [AC-4]', async () => {
    const user = userEvent.setup()
    const onChange = vi.fn()
    render(<UIRowTable {...props} items={ITEMS} min={1} max={5} onChange={onChange} />)

    await user.click(screen.getAllByRole('button', { name: 'Quitar' })[1])

    expect(onChange).toHaveBeenCalledWith([ITEMS[0], ITEMS[2]])
  })

  it('WHEN rows show as cards on narrow screens THEN they reuse the UICard surface (D-7)', () => {
    render(<UIRowTable {...props} items={ITEMS} min={1} max={5} onChange={vi.fn()} />)
    const row = screen.getAllByRole('button', { name: 'Quitar' })[0]?.closest('tr')
    for (const name of CARD_SURFACE.split(' ')) expect(row?.classList.contains(name)).toBe(true)
  })

  it('WHEN rows exist THEN each remove action shows an icon so it does not read as plain text (R-22)', () => {
    render(<UIRowTable {...props} items={ITEMS} min={1} max={5} onChange={vi.fn()} />)
    for (const button of screen.getAllByRole('button', { name: 'Quitar' })) expect(button.querySelector('svg')).not.toBeNull()
  })

  it('WHEN below min_rows THEN the counter shows how many are missing [AC-4]', () => {
    render(<UIRowTable {...props} items={ITEMS.slice(0, 1)} min={3} max={5} onChange={vi.fn()} />)

    expect(screen.getByText('Faltan 2')).toBeTruthy()
  })

  it('WHEN a field cell is rendered THEN it carries its column name for the card layout [R-20]', () => {
    render(<UIRowTable {...props} items={ITEMS} min={1} max={5} onChange={vi.fn()} />)

    const table = screen.getByRole('table', { name: 'Hijos' })

    expect(within(table).getByRole('cell', { name: 'Beto' }).getAttribute('data-label')).toBe('Nombre')
  })

  it('WHEN the card is narrower than 48 rem THEN its rows read as cards and the table starts at @3xl [R-15]', () => {
    render(<UIRowTable {...props} items={ITEMS} min={1} max={5} onChange={vi.fn()} />)

    const table = screen.getByRole('table', { name: 'Hijos' })

    expect(table.className).toContain('@3xl:table')
    expect(table.className).not.toContain('@xl:table')
  })
})

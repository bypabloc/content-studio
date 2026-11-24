import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { UIRepeatGroup } from '@/shared/components/organisms/UIRepeatGroup'

type Row = { _row: string; name: string }

const ITEMS: Row[] = [
  { _row: 'a', name: 'Ana' },
  { _row: 'b', name: 'Beto' },
  { _row: 'c', name: 'Carla' },
]

const props = {
  label: 'Hijos',
  addLabel: 'Agregar otro',
  removeLabel: 'Quitar',
  missingLabel: (missing: number) => `Faltan ${missing}`,
  createItem: (): Row => ({ _row: 'new', name: '' }),
  renderItem: (item: Row) => <span>{item.name}</span>,
}

describe('UIRepeatGroup [AC-4]', () => {
  it('WHEN below min_rows THEN the counter shows how many are missing [AC-4]', () => {
    render(<UIRepeatGroup {...props} items={ITEMS.slice(0, 1)} min={3} max={5} onChange={vi.fn()} />)

    expect(screen.getByText('Faltan 2')).toBeTruthy()
  })

  it('WHEN rows are added up to max_rows THEN the add button is disabled [AC-4]', () => {
    render(<UIRepeatGroup {...props} items={ITEMS} min={1} max={3} onChange={vi.fn()} />)

    expect(screen.getByRole('button', { name: 'Agregar otro' }).hasAttribute('disabled')).toBe(true)
  })

  it('WHEN a middle row is removed THEN the other rows keep their _row and values [AC-4]', async () => {
    const user = userEvent.setup()
    const onChange = vi.fn()
    render(<UIRepeatGroup {...props} items={ITEMS} min={1} max={5} onChange={onChange} />)

    await user.click(screen.getAllByRole('button', { name: 'Quitar' })[1])

    expect(onChange).toHaveBeenCalledWith([ITEMS[0], ITEMS[2]])
  })

  it('WHEN rows exist THEN each remove action shows an icon so it does not read as plain text (R-22)', () => {
    render(<UIRepeatGroup {...props} items={ITEMS} min={1} max={5} onChange={vi.fn()} />)
    for (const button of screen.getAllByRole('button', { name: 'Quitar' })) expect(button.querySelector('svg')).not.toBeNull()
  })

  it('WHEN rows exist THEN each one is a UICard region with its own remove action [AC-4]', () => {
    render(<UIRepeatGroup {...props} items={ITEMS.slice(0, 2)} min={1} max={5} onChange={vi.fn()} />)

    const cards = screen.getAllByRole('region')
    expect(cards).toHaveLength(2)
    expect(cards[0].textContent).toContain('Ana')
    expect(cards[0].querySelector('button')?.textContent).toBe('Quitar')
  })

  it('WHEN a row is added THEN the row from createItem is appended [AC-4]', async () => {
    const user = userEvent.setup()
    const onChange = vi.fn()
    render(<UIRepeatGroup {...props} items={ITEMS.slice(0, 1)} min={1} max={3} onChange={onChange} />)

    await user.click(screen.getByRole('button', { name: 'Agregar otro' }))

    expect(onChange).toHaveBeenCalledWith([ITEMS[0], { _row: 'new', name: '' }])
  })
})

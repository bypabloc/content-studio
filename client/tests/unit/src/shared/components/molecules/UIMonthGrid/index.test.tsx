import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import type { ComponentProps } from 'react'
import { describe, expect, it, vi } from 'vitest'

import { type MonthDay, UIMonthGrid } from '@/shared/components/molecules/UIMonthGrid'

type Props = ComponentProps<typeof UIMonthGrid>

const WEEKDAYS = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']
const ITEMS = [1, 2, 3, 4, 5].map((n) => ({ id: `APT-${n}`, text: `Cita ${n}` }))

/** One week, Monday 5 to Sunday 11 of March 2035; the 5 is busy and the 7 is today. */
const DAYS: MonthDay[] = Array.from({ length: 7 }, (_, i) => ({
  date: `2035-03-${String(5 + i).padStart(2, '0')}`,
  label: String(5 + i),
  outside: i === 6,
  today: i === 2,
  items: i === 0 ? ITEMS : [],
  more: i === 0 ? '+2 más' : undefined,
}))

function renderMonth(overrides: Partial<Props> = {}): void {
  render(<UIMonthGrid caption="Marzo de 2035" weekdays={WEEKDAYS} days={DAYS} todayText="hoy" onDaySelect={vi.fn()} onItemSelect={vi.fn()} {...overrides} />)
}

describe('UIMonthGrid', () => {
  it('WHEN a day has 5 items THEN shows 3 and the more text [AC-17]', () => {
    renderMonth()
    const grid = screen.getByRole('grid',{ name: 'Marzo de 2035' })
    expect(within(grid).getByRole('button', { name: 'Cita 3' })).toBeTruthy()
    expect(within(grid).queryByRole('button', { name: 'Cita 4' })).toBeNull()
    expect(within(grid).getByText('+2 más')).toBeTruthy()
  })

  it('WHEN selecting a day THEN onDaySelect receives its date [AC-17]', async () => {
    const user = userEvent.setup()
    const onDaySelect = vi.fn()
    renderMonth({ onDaySelect })
    await user.click(within(screen.getByRole('grid',{ name: 'Marzo de 2035' })).getByRole('button', { name: '6' }))
    expect(onDaySelect).toHaveBeenCalledWith('2035-03-06')
  })

  it('WHEN selecting an item THEN onItemSelect receives its id [AC-17]', async () => {
    const user = userEvent.setup()
    const onItemSelect = vi.fn()
    renderMonth({ onItemSelect })
    await user.click(within(screen.getByRole('grid',{ name: 'Marzo de 2035' })).getByRole('button', { name: 'Cita 2' }))
    expect(onItemSelect).toHaveBeenCalledWith('APT-2')
  })

  it('WHEN a day is today THEN its name says so as text too [AC-17]', () => {
    renderMonth()
    expect(within(screen.getByRole('grid',{ name: 'Marzo de 2035' })).getByRole('button', { name: '7 hoy' })).toBeTruthy()
  })

  it('WHEN a day is outside the month THEN the grid and list mark it as adjacent [AC-17]', () => {
    renderMonth()
    const grid = screen.getByRole('grid', { name: 'Marzo de 2035' })
    const tableCell = within(grid).getByRole('button', { name: '11' }).closest('[role="gridcell"]')
    expect(tableCell?.className).toContain('bg-muted')

    const list = screen.getByRole('list', { name: 'Marzo de 2035' })
    const listItem = within(list).getByRole('button', { name: 'Dom 11' }).closest('[role="listitem"]')
    expect(listItem?.className).toContain('text-muted-foreground')
  })

  it('WHEN narrow THEN each day is also listed with its weekday [AC-17]', () => {
    renderMonth()
    expect(within(screen.getByRole('list', { name: 'Marzo de 2035' })).getByRole('button', { name: 'Mar 6' })).toBeTruthy()
  })

  it('WHEN a weekday label is missing THEN the listed day still has its number [AC-17]', () => {
    renderMonth({ weekdays: [] })
    expect(within(screen.getByRole('list', { name: 'Marzo de 2035' })).getByRole('button', { name: '6' })).toBeTruthy()
  })
})

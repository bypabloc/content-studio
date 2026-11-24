import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { UIPagination } from '@/shared/components/molecules/UIPagination'

const labels = { nav: 'Paginación', previous: 'Anterior', next: 'Siguiente' }

describe('UIPagination [AC-9]', () => {
  it('WHEN on the first page THEN visible summary, previous disabled and next advances', async () => {
    const user = userEvent.setup()
    const onChange = vi.fn()
    render(<UIPagination total={45} limit={20} offset={0} onChange={onChange} summary="Mostrando 1–20 de 45" labels={labels} />)

    expect(screen.getByRole('navigation', { name: 'Paginación' })).toBeTruthy()
    expect(screen.getByText('Mostrando 1–20 de 45')).toBeTruthy()
    expect(screen.getByRole<HTMLButtonElement>('button', { name: 'Anterior' }).disabled).toBe(true)
    await user.click(screen.getByRole('button', { name: 'Siguiente' }))

    expect(onChange).toHaveBeenCalledWith(20)
  })

  it('WHEN on the last page THEN next disabled and previous goes back', async () => {
    const user = userEvent.setup()
    const onChange = vi.fn()
    render(<UIPagination total={45} limit={20} offset={40} onChange={onChange} summary="Mostrando 41–45 de 45" labels={labels} />)

    expect(screen.getByRole<HTMLButtonElement>('button', { name: 'Siguiente' }).disabled).toBe(true)
    await user.click(screen.getByRole('button', { name: 'Anterior' }))

    expect(onChange).toHaveBeenCalledWith(20)
  })

  it('WHEN everything fits in one page THEN only the summary shows, without dead buttons [AC-6.10]', () => {
    render(<UIPagination total={12} limit={20} offset={0} onChange={vi.fn()} summary="Mostrando 1–12 de 12" labels={labels} />)

    expect(screen.getByText('Mostrando 1–12 de 12')).toBeTruthy()
    expect(screen.queryByRole('button', { name: 'Anterior' })).toBeNull()
    expect(screen.queryByRole('button', { name: 'Siguiente' })).toBeNull()
  })
})

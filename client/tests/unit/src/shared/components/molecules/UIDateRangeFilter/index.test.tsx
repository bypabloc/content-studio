import { fireEvent, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { aIso, presetRange, UIDateRangeFilter } from '@/shared/components/molecules/UIDateRangeFilter'

const TODAY = new Date(2026, 8, 30)
const LABELS = { from: 'Desde', to: 'Hasta', presets: 'Rangos rápidos', '30d': '30 días', '90d': '90 días', '12m': '12 meses', year: 'Año actual', error: 'Hasta debe ser posterior a desde' }

const filter = (from = '2026-01-01', to = '2026-09-30', onChange = vi.fn()): ReturnType<typeof render> =>
  render(<UIDateRangeFilter from={from} to={to} onChange={onChange} today={TODAY} labels={LABELS} />)

describe('UIDateRangeFilter [AC-9]', () => {
  it('WHEN presetRange THEN ranges computed from today in local date', () => {
    expect(presetRange('30d', TODAY)).toEqual({ from: '2026-08-31', to: '2026-09-30' })
    expect(presetRange('90d', TODAY)).toEqual({ from: '2026-07-02', to: '2026-09-30' })
    expect(presetRange('12m', TODAY)).toEqual({ from: '2025-09-30', to: '2026-09-30' })
    expect(presetRange('year', TODAY)).toEqual({ from: '2026-01-01', to: '2026-09-30' })
    expect(aIso(new Date(2026, 0, 5))).toBe('2026-01-05')
  })

  it('WHEN preset 90 days THEN onChange(from, to) instantly', async () => {
    const onChange = vi.fn()
    filter(undefined, undefined, onChange)

    await userEvent.click(screen.getByRole('button', { name: '90 días' }))
    expect(onChange).toHaveBeenCalledWith('2026-07-02', '2026-09-30')
  })

  it('WHEN the value matches a preset THEN aria-pressed', () => {
    filter('2026-01-01', '2026-09-30')

    expect(screen.getByRole('button', { name: 'Año actual' }).getAttribute('aria-pressed')).toBe('true')
    expect(screen.getByRole('button', { name: '30 días' }).getAttribute('aria-pressed')).toBe('false')
  })

  it('WHEN to < from THEN error next to the field and no onChange', () => {
    const onChange = vi.fn()
    filter(undefined, undefined, onChange)

    const to = screen.getByLabelText('Hasta')
    fireEvent.change(to, { target: { value: '2025-12-01' } })
    expect(onChange).not.toHaveBeenCalled()
    expect(to.getAttribute('aria-invalid')).toBe('true')
    expect(screen.getByText('Hasta debe ser posterior a desde')).toBeTruthy()
  })

  it('WHEN the range is longer than maxDays THEN it explains the limit and does not call onChange [AC-6.7]', () => {
    const onChange = vi.fn()
    render(<UIDateRangeFilter from="2026-01-01" to="2026-02-01" onChange={onChange} today={TODAY} maxDays={1098} labels={{ ...LABELS, tooLong: 'Rango demasiado largo' }} />)

    fireEvent.change(screen.getByLabelText('Desde'), { target: { value: '2015-01-01' } })
    expect(onChange).not.toHaveBeenCalled()
    expect(screen.getByText('Rango demasiado largo')).toBeTruthy()
  })

  it('WHEN a date is edited by hand to an inverted range THEN onEdit gets it and onChange does not [AC-10]', () => {
    const onChange = vi.fn()
    const onEdit = vi.fn()
    render(<UIDateRangeFilter from="2026-01-01" to="2026-09-30" onChange={onChange} onEdit={onEdit} today={TODAY} labels={LABELS} />)

    fireEvent.change(screen.getByLabelText('Hasta'), { target: { value: '2025-12-01' } })
    expect(onEdit).toHaveBeenCalledWith({ from: '2026-01-01', to: '2025-12-01' })
    expect(onChange).not.toHaveBeenCalled()
  })

  it('WHEN from changes to a valid date THEN onChange', () => {
    const onChange = vi.fn()
    filter(undefined, undefined, onChange)

    fireEvent.change(screen.getByLabelText('Desde'), { target: { value: '2026-03-01' } })
    expect(onChange).toHaveBeenCalledWith('2026-03-01', '2026-09-30')
  })

  it('WHEN the props change THEN the draft resyncs', () => {
    const { rerender } = filter()
    fireEvent.change(screen.getByLabelText('Hasta'), { target: { value: '2025-12-01' } })

    rerender(<UIDateRangeFilter from="2026-02-01" to="2026-02-28" onChange={vi.fn()} today={TODAY} labels={LABELS} />)
    expect((screen.getByLabelText('Hasta') as HTMLInputElement).value).toBe('2026-02-28')
    expect(screen.queryByText('Hasta debe ser posterior a desde')).toBeNull()
  })
})

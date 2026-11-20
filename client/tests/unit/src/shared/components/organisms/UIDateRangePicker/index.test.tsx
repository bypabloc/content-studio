import { act, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { UIDateRangePicker } from '@/shared/components/organisms/UIDateRangePicker'

const TODAY = new Date(Date.UTC(2026, 9, 31, 12))
const LABELS = {
  placeholder: 'Elegir rango',
  apply: 'Aplicar',
  cancel: 'Cancelar',
  clear: 'Limpiar',
  previous: 'Retroceder un mes',
  next: 'Avanzar un mes',
  from: 'Desde',
  to: 'Hasta',
  days: (count: number) => `${count} días`,
  presets: {
    today: 'Hoy',
    yesterday: 'Ayer',
    last7: 'Últimos 7 días',
    last30: 'Últimos 30 días',
    thisMonth: 'Este mes',
    lastMonth: 'Mes anterior',
  },
}

/** Renderiza el selector con «hoy» fijo y devuelve el espía de `onChange`. */
const renderPicker = (props: { value?: { from: string; to: string } | null; max?: string; today?: Date } = {}) => {
  const onChange = vi.fn()
  render(<UIDateRangePicker value={props.value ?? null} onChange={onChange} max={props.max} today={props.today ?? TODAY} labels={LABELS} />)
  return { onChange }
}

/** Botón del día con esa fecha ISO; falla si el día no está en pantalla. */
const day = (iso: string): HTMLElement => {
  const element = document.querySelector<HTMLElement>(`[data-iso="${iso}"]`)
  if (!element) throw new Error(`day ${iso} is not rendered`)
  return element
}

/** Abre el panel desde el disparador. */
const openPanel = async (user: ReturnType<typeof userEvent.setup>): Promise<void> => {
  await user.click(screen.getByRole('button', { name: LABELS.placeholder }))
}

describe('UIDateRangePicker [AC-35]', () => {
  it('WHEN opened THEN two consecutive months and six presets [AC-35]', async () => {
    renderPicker()
    await openPanel(userEvent.setup())
    const grids = screen.getAllByRole('grid')
    expect(grids).toHaveLength(2)
    expect(grids[0]?.getAttribute('aria-label')).toBe('octubre de 2026')
    expect(grids[1]?.getAttribute('aria-label')).toBe('noviembre de 2026')
    for (const name of Object.values(LABELS.presets)) {
      expect(screen.getByRole('button', { name })).toBeTruthy()
    }
  })

  it('WHEN only the start is picked THEN Apply is disabled and hovering paints the tentative range [AC-35]', async () => {
    renderPicker()
    const user = userEvent.setup()
    await openPanel(user)
    await user.click(day('2026-10-05'))
    await user.hover(day('2026-10-09'))
    expect(day('2026-10-07').getAttribute('data-state')).toBe('preview')
    expect((screen.getByRole('button', { name: LABELS.apply }) as HTMLButtonElement).disabled).toBe(true)
  })

  it('WHEN the end is before the start THEN they swap [AC-35]', async () => {
    const { onChange } = renderPicker()
    const user = userEvent.setup()
    await openPanel(user)
    await user.click(day('2026-10-09'))
    await user.click(day('2026-10-03'))
    await user.click(screen.getByRole('button', { name: LABELS.apply }))
    expect(onChange).toHaveBeenCalledWith({ from: '2026-10-03', to: '2026-10-09' })
  })

  it('WHEN Apply THEN onChange with ISO dates and closes [AC-35]', async () => {
    const { onChange } = renderPicker()
    const user = userEvent.setup()
    await openPanel(user)
    await user.click(day('2026-10-05'))
    await user.click(day('2026-10-09'))
    await user.click(screen.getByRole('button', { name: LABELS.apply }))
    expect(onChange).toHaveBeenCalledWith({ from: '2026-10-05', to: '2026-10-09' })
    await waitFor(() => expect(screen.queryAllByRole('grid')).toHaveLength(0))
  })

  it('WHEN Cancel or Escape THEN closes without onChange [AC-35]', async () => {
    const { onChange } = renderPicker()
    const user = userEvent.setup()
    await openPanel(user)
    await user.click(day('2026-10-05'))
    await user.click(screen.getByRole('button', { name: LABELS.cancel }))
    await waitFor(() => expect(screen.queryAllByRole('grid')).toHaveLength(0))
    await openPanel(user)
    await user.keyboard('{Escape}')
    await waitFor(() => expect(screen.queryAllByRole('grid')).toHaveLength(0))
    expect(onChange).not.toHaveBeenCalled()
  })

  it('WHEN arrow keys THEN focus moves by day [AC-35]', async () => {
    renderPicker()
    const user = userEvent.setup()
    await openPanel(user)
    act(() => day('2026-10-31').focus())
    await user.keyboard('{ArrowLeft}')
    expect(document.activeElement).toBe(day('2026-10-30'))
    await user.keyboard('{ArrowDown}')
    expect(document.activeElement).toBe(day('2026-11-06'))
  })

  it('WHEN a preset passes max THEN the draft is clamped and Apply sends it [AC-35]', async () => {
    const { onChange } = renderPicker({ max: '2026-10-30' })
    const user = userEvent.setup()
    await openPanel(user)
    await user.click(screen.getByRole('button', { name: LABELS.presets.thisMonth }))
    await user.click(screen.getByRole('button', { name: LABELS.apply }))
    expect(onChange).toHaveBeenCalledWith({ from: '2026-10-01', to: '2026-10-30' })
  })

  it('WHEN a range is set THEN the trigger shows full dates and its length, and Limpiar clears it [AC-35]', async () => {
    const { onChange } = renderPicker({ value: { from: '2026-10-01', to: '2026-10-31' } })
    const medium = (iso: string): string => new Intl.DateTimeFormat('es', { dateStyle: 'medium' }).format(new Date(`${iso}T00:00:00`))
    const user = userEvent.setup()
    const trigger = screen.getByRole('button', { name: new RegExp(medium('2026-10-01')) })
    expect(trigger.textContent).toBe(`${medium('2026-10-01')} – ${medium('2026-10-31')} · 31 días`)
    await user.click(screen.getByRole('button', { name: LABELS.clear }))
    expect(onChange).toHaveBeenCalledWith(null)
  })

  it('WHEN a preset is pressed THEN only that preset is marked as pressed', async () => {
    renderPicker()
    const user = userEvent.setup()
    await openPanel(user)
    await user.click(screen.getByRole('button', { name: LABELS.presets.lastMonth }))
    const pressed = Object.values(LABELS.presets).filter((name) => screen.getByRole('button', { name }).getAttribute('aria-pressed') === 'true')
    expect(pressed).toEqual([LABELS.presets.lastMonth])
    await user.click(day('2026-10-05'))
    expect(screen.getByRole('button', { name: LABELS.presets.lastMonth }).getAttribute('aria-pressed')).toBe('false')
  })

  it('WHEN the dates are typed THEN Apply sends them in order', async () => {
    const { onChange } = renderPicker()
    const user = userEvent.setup()
    await openPanel(user)
    const from = screen.getByLabelText(LABELS.from) as HTMLInputElement
    const to = screen.getByLabelText(LABELS.to) as HTMLInputElement
    expect(from.type).toBe('date')
    await user.type(to, '2026-10-02')
    await user.type(from, '2026-10-20')
    await user.click(screen.getByRole('button', { name: LABELS.apply }))
    expect(onChange).toHaveBeenCalledWith({ from: '2026-10-02', to: '2026-10-20' })
  })

  it('WHEN opened THEN the second month is only shown from the sm breakpoint and the panel is capped at 42rem', async () => {
    renderPicker()
    await openPanel(userEvent.setup())
    const second = screen.getAllByRole('grid')[1]?.parentElement
    expect(second?.className).toMatch(/\bhidden\b/)
    expect(second?.className).toMatch(/\bsm:flex\b/)
    expect(document.querySelector('[data-range-panel]')?.className).toMatch(/\bmax-w-2xl\b/)
  })

  it('WHEN the next or previous month is pressed THEN the calendar moves one month [AC-35]', async () => {
    renderPicker()
    const user = userEvent.setup()
    await openPanel(user)
    await user.click(screen.getByRole('button', { name: LABELS.next }))
    expect(screen.getAllByRole('grid')[0]?.getAttribute('aria-label')).toBe('noviembre de 2026')
    await user.click(screen.getByRole('button', { name: LABELS.previous }))
    expect(screen.getAllByRole('grid')[0]?.getAttribute('aria-label')).toBe('octubre de 2026')
  })

  it('WHEN Hoy is pressed after the UTC day has started THEN the range is that UTC day [AC-35]', async () => {
    const { onChange } = renderPicker({ today: new Date('2026-11-01T02:00:00Z') })
    const user = userEvent.setup()
    await openPanel(user)
    await user.click(screen.getByRole('button', { name: LABELS.presets.today }))
    await user.click(screen.getByRole('button', { name: LABELS.apply }))
    expect(onChange).toHaveBeenCalledWith({ from: '2026-11-01', to: '2026-11-01' })
  })

  it('WHEN a month is shown THEN each day button shows its UTC day number [AC-35]', async () => {
    renderPicker()
    await openPanel(userEvent.setup())
    expect(day('2026-10-01').textContent).toBe('1')
    expect(day('2026-10-31').textContent).toBe('31')
  })
})

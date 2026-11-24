import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { UIDateParts } from '@/shared/components/molecules/UIDateParts'

const LABELS = { day: 'Día', month: 'Mes', year: 'Año' }
const VALUES = { day: '', month: '', year: '' }

describe('UIDateParts [AC-5]', () => {
  it('WHEN rendered THEN a group named by its label holds the day, month and year fields [AC-5]', () => {
    render(<UIDateParts label="Fecha de nacimiento" labels={LABELS} values={VALUES} onChange={vi.fn()} />)

    const group = screen.getByRole('group', { name: 'Fecha de nacimiento' })

    expect(within(group).getByRole('textbox', { name: 'Día' })).toBeTruthy()
    expect(within(group).getByRole('textbox', { name: 'Mes' })).toBeTruthy()
    expect(within(group).getByRole('textbox', { name: 'Año' })).toBeTruthy()
  })

  it('WHEN a part is typed THEN notifies the part and its value [AC-5]', async () => {
    const user = userEvent.setup()
    const onChange = vi.fn()
    render(<UIDateParts label="Fecha de nacimiento" labels={LABELS} values={VALUES} onChange={onChange} />)

    await user.type(screen.getByRole('textbox', { name: 'Mes' }), '3')

    expect(onChange).toHaveBeenCalledWith('month', '3')
  })
})

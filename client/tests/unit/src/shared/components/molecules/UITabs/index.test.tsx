import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { useState } from 'react'
import { describe, expect, it, vi } from 'vitest'

import { UITabs } from '@/shared/components/molecules/UITabs'

const ITEMS = [
  { value: 'summary', label: 'Summary' },
  { value: 'patients', label: 'Patients' },
]

/** Pestañas con estado propio, para cambiar de pestaña con un clic real. */
function Harness(): React.JSX.Element {
  const [value, setValue] = useState('summary')
  return (
    <UITabs value={value} onValueChange={setValue} label="Groups" items={ITEMS}>
      {`${value} content`}
    </UITabs>
  )
}

describe('UITabs', () => {
  it('WHEN rendered THEN labeled list, active tab and its content in the panel', () => {
    render(
      <UITabs value="patients" onValueChange={vi.fn()} label="Report groups" items={ITEMS}>
        patients content
      </UITabs>,
    )

    expect(screen.getByRole('tablist', { name: 'Report groups' })).toBeTruthy()
    const active = screen.getByRole('tab', { name: 'Patients' })
    expect(active.getAttribute('aria-selected')).toBe('true')
    expect(active.className).toContain('min-h-11')
    expect(screen.getByRole('tabpanel').textContent).toBe('patients content')
  })

  it('WHEN another tab is chosen THEN calls onValueChange with its value', async () => {
    const user = userEvent.setup()
    const onValueChange = vi.fn()
    render(
      <UITabs value="summary" onValueChange={onValueChange} label="Groups" items={ITEMS}>
        x
      </UITabs>,
    )

    await user.click(screen.getByRole('tab', { name: 'Patients' }))

    expect(onValueChange).toHaveBeenCalledWith('patients')
  })

  it('WHEN analytics are enabled THEN the selected tab carries its safe id and value', async () => {
    const user = userEvent.setup()
    render(
      <UITabs value="summary" onValueChange={vi.fn()} label="Groups" items={ITEMS} analyticsId="reports.tab">
        x
      </UITabs>,
    )

    const patientsTab = screen.getByRole('tab', { name: 'Patients' })
    expect(patientsTab.getAttribute('data-analytics')).toBe('reports.tab')
    expect(patientsTab.getAttribute('data-analytics-detail')).toBe('patients')
    await user.click(patientsTab)
  })

  it('WHEN the active tab changes THEN the panel is a new node with the fade class [AC-6]', async () => {
    const user = userEvent.setup()
    render(<Harness />)

    const before = screen.getByRole('tabpanel')
    await user.click(screen.getByRole('tab', { name: 'Patients' }))

    const after = screen.getByRole('tabpanel')
    expect(after.textContent).toBe('patients content')
    expect(after).not.toBe(before)
    expect(after.classList.contains('motion-safe:animate-ui-fade')).toBe(true)
  })

  it('WHEN the screen is narrow THEN the tab list wraps so every tab stays visible [AC-1.8]', () => {
    render(
      <UITabs value="summary" onValueChange={vi.fn()} label="Groups" items={ITEMS}>
        summary content
      </UITabs>,
    )

    const list = screen.getByRole('tablist', { name: 'Groups' })
    expect(list.className).toContain('max-sm:flex-wrap')
    expect(list.className).toContain('max-sm:w-full')
  })
})

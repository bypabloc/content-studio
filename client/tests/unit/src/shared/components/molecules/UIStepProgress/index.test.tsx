import { render, screen, within } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { UIStepProgress } from '@/shared/components/molecules/UIStepProgress'

const STEPS = ['Datos', 'Consentimiento', 'Revisión']

describe('UIStepProgress [AC-5]', () => {
  it('WHEN rendered THEN the list is named and only the current step is marked [AC-5]', () => {
    render(<UIStepProgress label="Progreso" steps={STEPS} current={1} />)

    const items = within(screen.getByRole('list', { name: 'Progreso' })).getAllByRole('listitem')

    expect(items).toHaveLength(STEPS.length)
    expect(items[1].getAttribute('aria-current')).toBe('step')
    expect(items[0].getAttribute('aria-current')).toBeNull()
  })

  it('WHEN rendered THEN every step name appears [AC-5]', () => {
    render(<UIStepProgress label="Progreso" steps={STEPS} current={0} />)

    for (const step of STEPS) {
      expect(screen.getByText(step)).toBeTruthy()
    }
  })

  it('WHEN rendered THEN every step has its own icon, so its state is not only its color [R-50]', () => {
    render(<UIStepProgress label="Progreso" steps={STEPS} current={1} />)

    const items = within(screen.getByRole('list', { name: 'Progreso' })).getAllByRole('listitem')

    for (const item of items) {
      expect(item.querySelector('svg')).not.toBeNull()
    }
  })
})

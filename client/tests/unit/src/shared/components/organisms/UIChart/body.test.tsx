import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { UIChartBody } from '@/shared/components/organisms/UIChart/body'

const DATA = [
  { x: 'pending', orders: 1, others: 2 },
  { x: 'sent', orders: 3, others: 1 },
]

// El cuerpo se prueba aquí sin la carga perezosa: `index.test.tsx` cubre la entrada y el esqueleto.
describe('UIChartBody', () => {
  it('WHEN drawn THEN it renders the figure with its accessible name', async () => {
    render(<UIChartBody kind="bar" data={DATA} xKey="x" series={[{ key: 'orders', label: 'Orders' }]} ariaLabel="Orders by status" />)

    expect(await screen.findByRole('figure', { name: 'Orders by status' })).toBeTruthy()
  })

  it('WHEN a series has the cross marker THEN the curve still renders', async () => {
    render(
      <UIChartBody kind="curves" data={[{ age: 0, p: 2 }, { age: 1, p: 3 }]} xKey="age" series={[{ key: 'p', label: 'P', marker: 'cross' }]} ariaLabel="Cruz" />,
    )

    expect(await screen.findByRole('figure', { name: 'Cruz' })).toBeTruthy()
  })
})

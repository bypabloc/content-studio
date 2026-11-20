import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { UIErrorSummary } from '@/shared/components/molecules/UIErrorSummary'

describe('UIErrorSummary [AC-6]', () => {
  it('WHEN errors exist THEN each one links to its field [AC-6]', () => {
    render(
      <UIErrorSummary
        title="Revisa estos campos"
        errors={[
          { id: 'other-text', message: 'Escribe el detalle de otro' },
          { id: 'age', message: 'Edad inválida' },
        ]}
      />,
    )

    expect(screen.getByRole('alert')).toBeTruthy()
    expect(screen.getByRole('link', { name: 'Escribe el detalle de otro' }).getAttribute('href')).toBe('#other-text')
  })

  it('WHEN there are no errors THEN nothing is rendered [AC-6]', () => {
    const { container } = render(<UIErrorSummary title="Revisa estos campos" errors={[]} />)

    expect(container.firstChild).toBeNull()
  })

  it('WHEN the summary appears THEN it takes focus so the errors are read first [AC-6]', () => {
    render(<UIErrorSummary title="Revisa estos campos" errors={[{ id: 'age', message: 'Edad inválida' }]} />)

    expect(screen.getByRole('alert')).toBe(document.activeElement)
  })
})

import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { UIStatus } from '@/shared/components/atoms/UIStatus'

describe('UIStatus', () => {
  it('announces only the label in a hidden live region and shows the visual content apart', () => {
    render(
      <UIStatus label="Loading…">
        <span>skeleton</span>
      </UIStatus>,
    )

    const status = screen.getByRole('status')
    expect(status.textContent).toBe('Loading…')
    expect(status.className).toContain('sr-only')
    expect(screen.getByText('skeleton')).toBeTruthy()
  })
})

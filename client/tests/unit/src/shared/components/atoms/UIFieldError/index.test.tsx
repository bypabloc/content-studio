import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { UIFieldError } from '@/shared/components/atoms/UIFieldError'

describe('UIFieldError [R-32]', () => {
  it('WHEN a message is given THEN it is announced as an alert with the given id [R-32]', () => {
    render(<UIFieldError id="q-repeat-error">Answer this question.</UIFieldError>)

    const alert = screen.getByRole('alert')
    expect(alert.id).toBe('q-repeat-error')
    expect(alert.textContent).toContain('Answer this question.')
  })

  it('WHEN a message is given THEN an icon sits beside the text so the error is not only colour [R-32]', () => {
    render(<UIFieldError>Write your name.</UIFieldError>)

    expect(screen.getByRole('alert').querySelector('svg')).not.toBeNull()
  })
})

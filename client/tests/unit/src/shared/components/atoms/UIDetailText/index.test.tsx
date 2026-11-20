import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { UIDetailText } from '@/shared/components/atoms/UIDetailText'

describe('UIDetailText [AC-34]', () => {
  it('WHEN rendered THEN the full value is its title and the short text is what is shown [AC-34]', () => {
    render(<UIDetailText full="arn:aws:rds:us-east-1:123456789012:db:klinikae-prod">klinikae-prod</UIDetailText>)
    expect(screen.getByTitle('arn:aws:rds:us-east-1:123456789012:db:klinikae-prod').textContent).toBe('klinikae-prod')
  })
})

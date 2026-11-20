import { render } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { UIHiddenInput } from '@/shared/components/atoms/UIHiddenInput'

describe('UIHiddenInput', () => {
  it('WHEN rendered in a form THEN a hidden field carries its name and value to the submitted data', () => {
    const { container } = render(
      <form>
        <UIHiddenInput name="diagnoses.0.diagnosis_code_id" value="0198f0a0-0000-7000-8000-000000000011" />
      </form>,
    )
    const form = container.querySelector('form') as HTMLFormElement
    const input = container.querySelector('input') as HTMLInputElement

    expect(input.type).toBe('hidden')
    expect(new FormData(form).get('diagnoses.0.diagnosis_code_id')).toBe('0198f0a0-0000-7000-8000-000000000011')
  })
})

import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { UISearchField } from '@/shared/components/molecules/UISearchField'

describe('UISearchField [AC-9]', () => {
  it('WHEN typing THEN notifies the text; search field with label and icon', async () => {
    const user = userEvent.setup()
    const onChange = vi.fn()
    const { container } = render(<UISearchField label="Buscar" value="" onChange={onChange} />)

    const input = screen.getByRole('searchbox', { name: 'Buscar' })
    await user.type(input, 'a')

    expect(onChange).toHaveBeenCalledWith('a')
    expect(container.querySelector('svg')).not.toBeNull()
  })
})

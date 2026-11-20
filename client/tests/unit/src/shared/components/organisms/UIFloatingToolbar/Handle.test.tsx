import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { FloatingToolbarHandle } from '@/shared/components/organisms/UIFloatingToolbar/Handle'

describe('FloatingToolbarHandle', () => {
  it('WHEN clicked THEN it reveals the bar and asks for focus on its first action', async () => {
    const onReveal = vi.fn()
    const user = userEvent.setup()
    render(<FloatingToolbarHandle label="Mostrar barra" className="top-0" vertical={false} onReveal={onReveal} />)

    await user.click(screen.getByRole('button', { name: 'Mostrar barra' }))

    expect(onReveal).toHaveBeenCalledWith(true)
  })

  it('WHEN the pointer enters THEN it reveals the bar without asking for focus', async () => {
    const onReveal = vi.fn()
    const user = userEvent.setup()
    render(<FloatingToolbarHandle label="Mostrar barra" className="top-0" vertical onReveal={onReveal} />)

    await user.hover(screen.getByRole('button', { name: 'Mostrar barra' }))

    expect(onReveal).toHaveBeenCalledWith()
  })
})

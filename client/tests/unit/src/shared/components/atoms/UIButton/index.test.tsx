import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import { UIButton } from '@/shared/components/atoms/UIButton'

describe('UIButton', () => {
  it('renders the content and fires onClick', () => {
    const onClick = vi.fn()
    render(<UIButton onClick={onClick}>Save</UIButton>)

    fireEvent.click(screen.getByRole('button', { name: 'Save' }))

    expect(onClick).toHaveBeenCalledOnce()
    expect(screen.getByRole('button').getAttribute('data-slot')).toBe('button')
  })

  it('WHEN loading THEN disabled, aria-busy and spinner instead of the icon', () => {
    const { container } = render(
      <UIButton loading icon="log-out">
        Save
      </UIButton>,
    )

    const button = screen.getByRole('button')
    expect(button).toHaveProperty('disabled', true)
    expect(button.getAttribute('aria-busy')).toBe('true')
    expect(container.querySelectorAll('svg')).toHaveLength(1)
    expect(container.querySelector('svg')?.getAttribute('class')).toContain('animate-spin')
  })

  it('WHEN secondary variant THEN uses border style and type button by default', () => {
    render(<UIButton variant="secondary">Exit</UIButton>)

    const button = screen.getByRole('button')
    expect(button.className).toContain('border')
    expect(button.getAttribute('type')).toBe('button')
  })

  it('WHEN block and icon THEN takes the full width and shows the decorative icon', () => {
    const { container } = render(
      <UIButton block variant="ghost" icon="log-out">
        Exit
      </UIButton>,
    )

    expect(screen.getByRole('button').className).toContain('w-full')
    expect(container.querySelector('svg')?.getAttribute('aria-hidden')).toBe('true')
  })

  it('WHEN hideLabelOnMobile THEN the text stays only for screen readers on mobile and keeps the accessible name', () => {
    render(
      <UIButton icon="log-out" hideLabelOnMobile>
        Exit
      </UIButton>,
    )

    const button = screen.getByRole('button', { name: 'Exit' })
    expect(screen.getByText('Exit').className).toContain('max-sm:sr-only')
    expect(button.className).toContain('max-sm:px-0')
  })

  it('WHEN the button is enabled THEN it has the ui-press class [AC-3]', () => {
    render(<UIButton>Save</UIButton>)

    expect(screen.getByRole('button', { name: 'Save' }).classList.contains('ui-press')).toBe(true)
  })

  it('WHEN the button is disabled THEN it has no ui-press class [AC-3]', () => {
    render(<UIButton disabled>Save</UIButton>)

    expect(screen.getByRole('button', { name: 'Save' }).classList.contains('ui-press')).toBe(false)
  })

  it('WHEN the button is disabled THEN it keeps readable contrast tokens', () => {
    render(<UIButton disabled>Save</UIButton>)

    const button = screen.getByRole('button', { name: 'Save' })
    expect(button.className).toContain('disabled:bg-muted')
    expect(button.className).toContain('disabled:text-muted-foreground')
    expect(button.className).not.toContain('disabled:opacity-50')
  })

  it('WHEN the button is loading THEN it has no ui-press class [AC-3]', () => {
    render(<UIButton loading>Save</UIButton>)

    expect(screen.getByRole('button').classList.contains('ui-press')).toBe(false)
  })

  it('WHEN variant is danger THEN it uses the solid destructive tone [AC-1.7]', () => {
    render(<UIButton variant="danger">Void</UIButton>)

    const button = screen.getByRole('button', { name: 'Void' })
    expect(button.className).toContain('bg-destructive')
    expect(button.className).toContain('text-card')
    expect(button.className).toContain('dark:bg-destructive ')
    expect(button.className).not.toContain('dark:bg-destructive/20')
  })

  it('WHEN the text is longer than its container THEN it wraps inside the button [AC-1.6]', () => {
    render(<UIButton>Sign out on every device</UIButton>)

    const button = screen.getByRole('button')
    expect(button.className).toContain('whitespace-normal')
    expect(button.className).toContain('max-w-full')
    expect(button.className).toContain('text-center')
  })
})

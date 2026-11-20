import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { nextTheme, type Theme, THEME_ICONS, toTheme, UIThemeToggle } from '@/shared/components/molecules/UIThemeToggle'

const LABELS = { toggle: 'Tema', light: 'Claro', dark: 'Oscuro', system: 'Sistema' }

describe('UIThemeToggle [AC-6]', () => {
  it.each<[Theme, Theme]>([
    ['light', 'dark'],
    ['dark', 'system'],
    ['system', 'light'],
  ])('WHEN clicked on %s THEN switches to %s without opening a menu', async (current, next) => {
    const user = userEvent.setup()
    const onThemeChange = vi.fn()
    render(<UIThemeToggle theme={current} onThemeChange={onThemeChange} labels={LABELS} />)

    const button = screen.getByRole('button', { name: 'Tema' })
    await user.click(button)

    expect(onThemeChange).toHaveBeenCalledWith(next)
    expect(screen.queryByRole('menu')).toBeNull()
  })

  it('WHEN a preference is given THEN its icon shows it and the tooltip names the toggle (AC-2, AC-4)', async () => {
    const user = userEvent.setup()
    render(<UIThemeToggle theme="dark" onThemeChange={vi.fn()} labels={LABELS} />)

    const button = screen.getByRole('button', { name: 'Tema' })
    expect(button.querySelector('svg')?.getAttribute('class')).toContain('lucide-moon')
    await user.tab()
    expect((await screen.findByRole('tooltip')).textContent).toBe('Tema')
  })

  it('WHEN a visible label is given THEN it is shown and the button keeps the toggle name', () => {
    render(<UIThemeToggle theme="light" onThemeChange={vi.fn()} labels={LABELS} visibleLabel="Claro" />)

    const button = screen.getByRole('button', { name: 'Tema' })
    expect(button.textContent).toContain('Claro')
  })

  it('WHEN a preference is shown THEN its icon is the theme-* name of spec 009 (AC-2)', () => {
    expect(THEME_ICONS).toEqual({ light: 'theme-light', dark: 'theme-dark', system: 'theme-system' })
  })

  it('WHEN cycling THEN light → dark → system → light', () => {
    expect(nextTheme('light')).toBe('dark')
    expect(nextTheme('dark')).toBe('system')
    expect(nextTheme('system')).toBe('light')
  })

  it('WHEN the saved preference is invalid or not yet known THEN it is treated as system', () => {
    expect(toTheme('dark')).toBe('dark')
    expect(toTheme('rosa')).toBe('system')
    expect(toTheme(undefined)).toBe('system')
  })
})

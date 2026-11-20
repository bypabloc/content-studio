import { fireEvent, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { type NavEntry, UIAppShell } from '@/shared/components/organisms/UIAppShell'

const LABELS = { skip: 'Saltar al contenido', toggle: 'Mostrar u ocultar el menú', title: 'Navegación' }
const NAV: NavEntry[] = [
  { id: 'narration', group: 'Generar', label: 'Narración', icon: 'mic' },
  { id: 'settings', group: 'Ajustes', label: 'Preferencias', icon: 'settings' },
]

const shell = (props: Partial<Parameters<typeof UIAppShell>[0]> = {}) =>
  render(
    <UIAppShell brand={<span>marca</span>} nav={NAV} labels={LABELS} {...props}>
      <span>contenido</span>
    </UIAppShell>,
  )

// Sin modo móvil: la barra lateral colapsa a íconos, con la misma navegación, en cualquier ancho.
describe('UIAppShell [AC-7]', () => {
  afterEach(() => {
    window.location.hash = ''
  })

  it('WHEN rendered THEN it has the skip link, the grouped navigation and the main content', () => {
    shell()

    expect(screen.getByRole('link', { name: LABELS.skip }).getAttribute('href')).toBe('#content')
    const nav = screen.getByRole('navigation', { name: LABELS.title })
    expect(nav.textContent).toContain('Generar')
    expect(nav.textContent).toContain('Ajustes')
    expect(screen.getByRole('link', { name: 'Narración' }).getAttribute('href')).toBe('#/narration')
    expect(screen.getByRole('main').textContent).toBe('contenido')
  })

  it('WHEN the hash names a section THEN that item is the current page', () => {
    window.location.hash = '#/settings'

    shell()

    expect(screen.getByRole('link', { name: 'Preferencias' }).getAttribute('aria-current')).toBe('page')
    expect(screen.getByRole('link', { name: 'Narración' }).getAttribute('aria-current')).toBeNull()
  })

  it('WHEN the toggle is pressed THEN the sidebar collapses and reports the new state', async () => {
    const user = userEvent.setup()
    const onCollapsedChange = vi.fn()
    shell({ collapsed: false, onCollapsedChange })

    await user.click(screen.getByRole('button', { name: LABELS.toggle }))

    expect(onCollapsedChange).toHaveBeenCalledWith(true)
  })

  it('WHEN Ctrl+B is pressed THEN the sidebar toggles like the button', () => {
    const onCollapsedChange = vi.fn()
    shell({ collapsed: true, onCollapsedChange })

    fireEvent.keyDown(window, { key: 'b', ctrlKey: true })

    expect(onCollapsedChange).toHaveBeenCalledWith(false)
  })

  it('WHEN the saved state is collapsed (ui.sidebar.collapsed) THEN the sidebar starts in icon mode', () => {
    const { container } = shell({ collapsed: true })

    expect(container.querySelector('[data-collapsible="icon"]')).not.toBeNull()
  })

  it('WHEN collapsed THEN the items keep their names and show a tooltip on hover', async () => {
    const user = userEvent.setup()
    shell({ collapsed: true })

    await user.hover(screen.getByRole('link', { name: 'Narración' }))

    expect(await screen.findByRole('tooltip')).toBeTruthy()
  })

  it('WHEN the shell renders THEN the queue panel (aside) and the footer sit inside the sidebar landmark', () => {
    shell({ aside: <span>cola</span>, footer: <span>tema y versión</span> })

    const sidebar = screen.getByRole('complementary')
    expect(sidebar.textContent).toContain('cola')
    expect(sidebar.textContent).toContain('tema y versión')
  })
})

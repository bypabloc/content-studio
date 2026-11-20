import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { UIDescriptionList } from '@/shared/components/molecules/UIDescriptionList'

// Sin `dl` nativa (spec 008, D-4): el grupo es role="list" y cada par, role="listitem" con su término y su detalle.
const LIST = '[role="list"]'

describe('UIDescriptionList', () => {
  it('cada par término-detalle es un ítem de la lista, con su término y su detalle', () => {
    render(<UIDescriptionList items={[{ icon: 'store', term: 'Tenant', detail: 'Clínica Central' }]} />)

    const item = screen.getByText('Tenant').closest('[role="listitem"]')
    expect(item).not.toBeNull()
    expect(item?.textContent).toContain('Clínica Central')
  })

  it('WHEN there are several pairs THEN each list item holds the term and the detail as its two blocks', () => {
    const { container } = render(
      <UIDescriptionList
        items={[
          { icon: 'store', term: 'Tenant', detail: 'Clínica Central' },
          { icon: 'user', term: 'Usuario', detail: 'ana' },
        ]}
      />,
    )

    const groups = [...(container.querySelector(LIST)?.children ?? [])]
    expect(groups).toHaveLength(2)
    for (const group of groups) {
      expect(group.getAttribute('role')).toBe('listitem')
      expect(group.children).toHaveLength(2)
    }
  })

  it('WHEN rendered THEN the list sits in a container and has one column by default [AC-27]', () => {
    const { container } = render(<UIDescriptionList items={[{ icon: 'store', term: 'Tenant', detail: 'Clínica Central' }]} />)
    const list = container.querySelector(LIST)

    expect(list?.className).toContain('grid-cols-1')
    expect(list?.parentElement?.className).toContain('@container')
  })

  it('WHEN the container reaches 32rem or 48rem THEN the list uses @lg and @3xl columns and no viewport breakpoint [AC-27]', () => {
    const { container } = render(<UIDescriptionList items={[{ icon: 'store', term: 'Tenant', detail: 'Clínica Central' }]} />)
    const list = container.querySelector(LIST)

    expect(list?.className).toContain('@lg:grid-cols-2')
    expect(list?.className).toContain('@3xl:grid-cols-3')
    expect(list?.className).not.toMatch(/(^|\s)(sm|lg):/)
  })

  it('WHEN an item renders THEN the icon sits inside its term, is aria-hidden and is not absolutely positioned [AC-28]', () => {
    const { container } = render(<UIDescriptionList items={[{ icon: 'store', term: 'Tenant', detail: 'Clínica Central' }]} />)
    const svg = screen.getByText('Tenant').querySelector('svg')

    expect(svg).not.toBeNull()
    expect(svg?.closest('[aria-hidden="true"]')).not.toBeNull()
    for (const el of container.querySelectorAll(`${LIST} *`)) {
      expect(el.getAttribute('class') ?? '').not.toMatch(/\b(absolute|relative|pl-17)\b/)
    }
  })

  it('WHEN the detail has spaces THEN it wraps with wrap-break-word and text-pretty [AC-29]', () => {
    render(<UIDescriptionList items={[{ icon: 'user', term: 'Profesional', detail: 'Elena Vásconez' }]} />)
    const detail = screen.getByText('Elena Vásconez')

    expect(detail.className).toContain('wrap-break-word')
    expect(detail.className).toContain('text-pretty')
    expect(detail.className).not.toContain('wrap-anywhere')
  })

  it('WHEN the detail is a list of lines THEN each line renders on its own block [AC-29]', () => {
    render(<UIDescriptionList items={[{ icon: 'clipboard-list', term: 'Velocidad', detail: ['Internet: Rápido', 'Correo: Lento'] }]} />)

    expect(screen.getByText('Internet: Rápido').tagName).toBe('SPAN')
    expect(screen.getByText('Correo: Lento').closest('[role="listitem"]')).not.toBeNull()
  })

  it('WHEN the detail is a list of lines THEN the lines are spaced apart so each row reads on its own [H11]', () => {
    render(<UIDescriptionList items={[{ icon: 'clipboard-list', term: 'Velocidad', detail: ['Internet: Rápido', 'Correo: Lento'] }]} />)

    expect(screen.getByText('Correo: Lento').parentElement?.className).toContain('space-y-1.5')
  })

  it('WHEN the detail is one string without spaces THEN it uses wrap-anywhere [AC-29]', () => {
    render(<UIDescriptionList items={[{ icon: 'mail', term: 'Correo', detail: 'elena.vasconez@central.test' }]} />)
    const detail = screen.getByText('elena.vasconez@central.test')

    expect(detail.className).toContain('wrap-anywhere')
    expect(detail.className).toContain('text-pretty')
    expect(detail.className).not.toContain('wrap-break-word')
  })

  it('WHEN rendered THEN every term and detail is a direct child of its list item [AC-28]', () => {
    const { container } = render(
      <UIDescriptionList
        items={[
          { icon: 'store', term: 'Tenant', detail: 'Clínica Central' },
          { icon: 'user', term: 'Usuario', detail: 'ana' },
        ]}
      />,
    )

    const groups = [...(container.querySelector(LIST)?.children ?? [])]
    expect(groups).toHaveLength(2)
    for (const group of groups) {
      expect(group.getAttribute('role')).toBe('listitem')
      expect(group.children).toHaveLength(2)
    }
  })
})

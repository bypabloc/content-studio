import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { UILink } from '@/shared/components/atoms/UILink'

describe('UILink', () => {
  it('WHEN rendered THEN it is a Next link with the destination and the attributes', () => {
    render(
      <UILink href="/patients" aria-current="page">
        dashboard
      </UILink>,
    )

    const link = screen.getByRole('link', { name: 'dashboard' })
    expect(link.getAttribute('href')).toBe('/patients')
    expect(link.getAttribute('aria-current')).toBe('page')
    expect(link.className).toBe('')
  })

  it.each([
    ['primary', 'bg-primary'],
    ['secondary', 'bg-card'],
    ['inline', 'underline-offset-4'],
  ] as const)('WHEN variant %s THEN action styles with visible focus and decorative icon', (variant, classValue) => {
    render(
      <UILink href="/patients/new" variant={variant} icon="plus" className="extra">
        New patient
      </UILink>,
    )

    const link = screen.getByRole('link', { name: 'New patient' })
    expect(link.className).toContain(classValue)
    expect(link.className).toContain('focus-visible:ui-focus')
    expect(link.className).toContain('extra')
    expect(link.querySelector('svg')?.getAttribute('aria-hidden')).toBe('true')
  })

  it('WHEN hideLabelOnMobile THEN the text stays only for screen readers on mobile and keeps the accessible name', () => {
    render(
      <UILink href="/portal/security" variant="secondary" icon="shield-check" hideLabelOnMobile>
        Security
      </UILink>,
    )

    const link = screen.getByRole('link', { name: 'Security' })
    expect(screen.getByText('Security').className).toContain('max-sm:sr-only')
    expect(link.className).toContain('max-sm:w-11')
    expect(link.className).toContain('max-sm:px-0')
  })

  it('WHEN newTab is set THEN the notice is announced after the text, opening in a new tab with noopener', () => {
    render(
      <UILink href="https://wa.me/593991595951" target="_blank" rel="noopener noreferrer" variant="primary" icon="send" newTab="(se abre en una pestaña nueva)">
        Open chat
      </UILink>,
    )

    const link = screen.getByRole('link', { name: 'Open chat (se abre en una pestaña nueva)' })
    expect(link.getAttribute('target')).toBe('_blank')
    expect(link.getAttribute('rel')).toContain('noopener')
    expect(link.textContent).toBe('Open chat (se abre en una pestaña nueva)')
    expect(screen.getByText('(se abre en una pestaña nueva)').className).toContain('sr-only')
  })

  it('WHEN newTab is not set THEN no notice is rendered', () => {
    render(<UILink href="/patients">dashboard</UILink>)

    expect(screen.getByRole('link', { name: 'dashboard' }).querySelector('.sr-only')).toBeNull()
  })

  it('WHEN hideLabelOnMobile is not set THEN the text is a direct child of the link', () => {
    render(
      <UILink href="/portal/security" variant="secondary" icon="shield-check">
        Security
      </UILink>,
    )

    const link = screen.getByRole('link', { name: 'Security' })
    expect(link.querySelector('span')).toBeNull()
    expect(link.className).not.toContain('max-sm:px-0')
  })

  it('WHEN a button-variant link is rendered THEN it has the ui-press class [AC-4]', () => {
    render(
      <>
        <UILink href="/patients/new" variant="primary">
          New patient
        </UILink>
        <UILink href="/portal/security" variant="secondary">
          Security
        </UILink>
      </>,
    )

    for (const name of ['New patient', 'Security']) {
      const link = screen.getByRole('link', { name })
      expect(link.classList.contains('ui-press')).toBe(true)
    }
  })

  it('WHEN an inline link is rendered THEN it has no ui-press class [AC-4]', () => {
    render(
      <UILink href="/patients" variant="inline">
        dashboard
      </UILink>,
    )

    expect(screen.getByRole('link', { name: 'dashboard' }).classList.contains('ui-press')).toBe(false)
  })
})

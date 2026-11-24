import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { UIBadge } from '@/shared/components/atoms/UIBadge'

describe('UIBadge', () => {
  it('WHEN default tone THEN neutral', () => {
    render(<UIBadge>Coming soon</UIBadge>)

    expect(screen.getByText('Coming soon').className).toContain('bg-muted')
    expect(screen.getByText('Coming soon').getAttribute('data-slot')).toBe('badge')
  })

  it('WHEN brand tone THEN uses the brand palette', () => {
    render(<UIBadge tone="brand">New</UIBadge>)

    expect(screen.getByText('New').className).toContain('bg-accent')
  })

  it('WHEN accent tone THEN uses the success palette', () => {
    render(<UIBadge tone="accent">Ready</UIBadge>)
    expect(screen.getByText('Ready').className).toContain('bg-success-soft')
  })

  it('WHEN danger tone THEN uses the error/alert palette', () => {
    render(<UIBadge tone="danger">Severe</UIBadge>)
    expect(screen.getByText('Severe').className).toContain('bg-destructive-soft')
  })

  it('WHEN icon THEN decorative SVG before the text', () => {
    render(<UIBadge tone="danger" icon="triangle-alert">Obesity</UIBadge>)

    const badge = screen.getByText('Obesity')
    const svg = badge.querySelector('svg')
    expect(svg?.getAttribute('aria-hidden')).toBe('true')
    expect(badge.firstElementChild).toBe(svg)
    expect(badge.className).toContain('text-destructive')
  })

  it('WHEN no icon THEN no SVG', () => {
    render(<UIBadge>Normal</UIBadge>)
    expect(screen.getByText('Normal').querySelector('svg')).toBeNull()
  })
})

import { render, screen, within } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { UIStatCard } from '@/shared/components/molecules/UIStatCard'

const BASE = { label: 'Pacientes nuevos', value: '1.240', description: 'Registrados en el rango', icon: 'users' } as const

const tone = (): string | null => screen.getByRole('region', { name: BASE.label }).querySelector('[data-tone]')?.getAttribute('data-tone') ?? null

describe('UIStatCard [AC-9]', () => {
  it('WHEN a dashboard id is provided THEN the region forwards both analytics attributes', () => {
    render(<UIStatCard {...BASE} data-analytics="dashboard.card" data-analytics-detail="kpis" />)

    const region = screen.getByRole('region', { name: BASE.label })
    expect(region.getAttribute('data-analytics')).toBe('dashboard.card')
    expect(region.getAttribute('data-analytics-detail')).toBe('kpis')
  })

  it('WHEN rendered THEN region named by the label with value and description', () => {
    render(<UIStatCard {...BASE} />)

    const region = screen.getByRole('region', { name: 'Pacientes nuevos' })
    expect(within(region).getByText('1.240').className).toContain('tabular-nums')
    expect(within(region).getByText('Registrados en el rango')).toBeTruthy()
    expect(region.querySelector('[data-tone]')).toBeNull()
    expect(screen.queryByRole('link')).toBeNull()
  })

  it('WHEN delta down with positiveIsGood=false THEN success tone and sr-only "down"', () => {
    render(<UIStatCard {...BASE} delta={{ value: '12%', direction: 'down', label: 'low', positiveIsGood: false }} />)

    expect(tone()).toBe('good')
    expect(screen.getByText('low').className).toContain('sr-only')
    expect(screen.getByText('12%').className).toContain('text-success')
  })

  it('WHEN delta up with positiveIsGood=false THEN destructive tone', () => {
    render(<UIStatCard {...BASE} delta={{ value: '5%', direction: 'up', label: 'sube', positiveIsGood: false }} />)

    expect(tone()).toBe('bad')
    expect(screen.getByText('5%').className).toContain('text-destructive')
  })

  it('WHEN delta up with positiveIsGood=true THEN success tone', () => {
    render(<UIStatCard {...BASE} delta={{ value: '5%', direction: 'up', label: 'sube', positiveIsGood: true }} />)
    expect(tone()).toBe('good')
  })

  it('WHEN delta flat THEN neutral tone', () => {
    render(<UIStatCard {...BASE} delta={{ value: '0%', direction: 'flat', label: 'sin cambio', positiveIsGood: true }} />)

    expect(tone()).toBe('flat')
    expect(screen.getByText('0%').className).toContain('text-muted-foreground')
  })

  it('WHEN href and linkLabel THEN link to the detail', () => {
    render(<UIStatCard {...BASE} href="/reports" linkLabel="Ver reporte" />)

    expect(screen.getByRole('link', { name: 'Ver reporte' }).getAttribute('href')).toBe('/reports')
  })

  it('WHEN the value is an amount THEN it is never split inside the number [AC-1.5]', () => {
    render(<UIStatCard {...BASE} value="$159.913,00" />)

    expect(screen.getByText('$159.913,00').className).toContain('wrap-break-word')
  })
})

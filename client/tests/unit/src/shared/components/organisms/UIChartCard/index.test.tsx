import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { UIChartCard } from '@/shared/components/organisms/UIChartCard'

const LABELS = {
  howToRead: 'Cómo leerla',
  showData: 'Ver datos',
  hideData: 'Ocultar datos',
  retry: 'Reintentar',
  error: 'No se pudo cargar',
  empty: 'Sin datos en el rango',
  emptyDescription: 'Prueba otro rango',
  loading: 'Cargando gráfica',
}
const TABLE = {
  columns: [
    { key: 'status', label: 'Estado' },
    { key: 'n', label: 'Órdenes', align: 'right' as const },
  ],
  rows: [
    { status: 'Pendiente', n: '1' },
    { status: 'Entregada', n: '2' },
  ],
}

const card = (state: 'loading' | 'empty' | 'error' | 'ready', onRetry = vi.fn()): ReturnType<typeof render> =>
  render(
    <UIChartCard title="Órdenes por estado" description="Estado actual" howToRead="Cada sector es un estado" state={state} onRetry={onRetry} table={TABLE} height={200} labels={LABELS}>
      <span>chart</span>
    </UIChartCard>,
  )

describe('UIChartCard [AC-8]', () => {
  it('WHEN ready THEN h3 title, description and the chart', () => {
    card('ready')

    const region = screen.getByRole('region', { name: 'Órdenes por estado' })
    expect(within(region).getByRole('heading', { level: 3, name: 'Órdenes por estado' })).toBeTruthy()
    expect(within(region).getByText('Estado actual')).toBeTruthy()
    expect(within(region).getByText('chart')).toBeTruthy()
  })

  it('WHEN loading THEN skeleton with the chart height and status', () => {
    const { container } = card('loading')

    expect(screen.getByRole('status').textContent).toBe('Cargando gráfica')
    expect(container.querySelector('[data-slot="chart-placeholder"]')?.getAttribute('height')).toBe('200')
    expect(screen.queryByRole('button', { name: 'Ver datos' })).toBeNull()
  })

  it('WHEN the state is ready THEN the content sits in a wrapper with the fade class [AC-8]', () => {
    card('ready')

    expect(screen.getByText('chart').parentElement?.className).toContain('motion-safe:animate-ui-fade')
  })

  it('WHEN the state is loading THEN the skeleton has no fade class [AC-8]', () => {
    const { container } = card('loading')

    const skeletons = Array.from(container.querySelectorAll('[data-slot="skeleton"]'))
    expect(skeletons.length).toBeGreaterThan(0)
    expect(skeletons.some((skeleton) => skeleton.closest('[class*="animate-ui-fade"]') !== null)).toBe(false)
  })

  it('WHEN empty THEN empty state with text', () => {
    card('empty')

    expect(screen.getByRole('heading', { name: 'Sin datos en el rango' })).toBeTruthy()
    expect(screen.getByText('Prueba otro rango')).toBeTruthy()
  })

  it('WHEN error THEN alert and retry calls onRetry', async () => {
    const onRetry = vi.fn()
    card('error', onRetry)

    expect(screen.getByRole('alert').textContent).toContain('No se pudo cargar')
    await userEvent.click(screen.getByRole('button', { name: 'Reintentar' }))
    expect(onRetry).toHaveBeenCalledOnce()
  })

  it('WHEN show data THEN table with the rows and toggles to hide', async () => {
    card('ready')

    const button = screen.getByRole('button', { name: 'Ver datos' })
    expect(button.getAttribute('aria-expanded')).toBe('false')
    await userEvent.click(button)
    const table = screen.getByRole('table', { name: 'Órdenes por estado' })
    expect(within(table).getByRole('row', { name: (name) => name.includes('Entregada 2') })).toBeTruthy()
    await userEvent.click(screen.getByRole('button', { name: 'Ocultar datos' }))
    expect(screen.queryByRole('table')).toBeNull()
  })

  it('WHEN how to read it THEN the collapsible opens the text', async () => {
    card('ready')

    await userEvent.click(screen.getByRole('button', { name: 'Cómo leerla' }))
    expect(await screen.findByText('Cada sector es un estado')).toBeTruthy()
  })
})

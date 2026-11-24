import { render, screen, within } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { UITimeline } from '@/shared/components/molecules/UITimeline'

describe('UITimeline', () => {
  it('WHEN there are entries THEN named ordered list, in the given order and date as time', () => {
    render(
      <UITimeline
        label="Historial"
        items={[
          { key: 2, dateTime: '2026-09-20T10:00:00Z', date: '20 sept 2026', children: 'Control' },
          { key: 1, dateTime: '2026-01-05T10:00:00Z', date: '5 ene 2026', children: 'Primera' },
        ]}
      />,
    )

    const list = screen.getByRole('list', { name: 'Historial' })
    const items = within(list).getAllByRole('listitem')
    expect(items.map((i) => i.textContent)).toEqual(['20 sept 2026Control', '5 ene 2026Primera'])
    expect(items[0]?.querySelector('time')?.getAttribute('datetime')).toBe('2026-09-20T10:00:00Z')
  })

  it('WHEN a timeline entry renders THEN its item has the enter class [AC-11]', () => {
    render(
      <UITimeline
        label="Historial"
        items={[
          { key: 2, dateTime: '2026-09-20T10:00:00Z', date: '20 sept 2026', children: 'Control' },
          { key: 1, dateTime: '2026-01-05T10:00:00Z', date: '5 ene 2026', children: 'Primera' },
        ]}
      />,
    )

    const items = within(screen.getByRole('list', { name: 'Historial' })).getAllByRole('listitem')
    expect(items.map((item) => item.className.includes('motion-safe:animate-ui-enter'))).toEqual([true, true])
  })
})

import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { useState } from 'react'
import { describe, expect, it, vi } from 'vitest'

import { UICombobox } from '@/shared/components/molecules/UICombobox'

type Item = { id: number; name: string }
const ITEMS: Item[] = [
  { id: 1, name: 'Aviador' },
  { id: 2, name: 'Clásico' },
]

function Demo({
  onSelect,
  onQuery,
  items = ITEMS,
  error,
  hint = 'Escribe para buscar',
  total,
  group,
  hasMore,
  onLoadMore,
  loading,
}: {
  onSelect: (i: Item) => void
  onQuery?: (text: string) => void
  items?: Item[]
  error?: string
  hint?: string
  total?: number
  group?: (i: Item) => { key: string; label: string }
  hasMore?: boolean
  onLoadMore?: () => void
  loading?: boolean
}): React.JSX.Element {
  const [q, setQ] = useState('')
  return (
    <UICombobox
      label="Producto"
      placeholder="Buscar"
      items={q ? items : total === 1 ? items : []}
      itemKey={(i) => i.id}
      itemLabel={(i) => i.name}
      renderItem={(i) => <span>{`${i.name} · stock`}</span>}
      onSelect={onSelect}
      query={q}
      onQueryChange={(text) => {
        onQuery?.(text)
        setQ(text)
      }}
      empty="Sin resultados"
      hint={hint || undefined}
      error={error}
      total={total}
      group={group}
      hasMore={hasMore}
      onLoadMore={onLoadMore}
      loadMoreLabel="Cargar más"
      loading={loading}
    />
  )
}

describe('UICombobox [AC-6]', () => {
  it('WHEN typing and choosing with the keyboard THEN onSelect with the item and clears the text', async () => {
    const onSelect = vi.fn()
    render(<Demo onSelect={onSelect} />)

    const input = screen.getByRole('combobox', { name: 'Producto' })
    await userEvent.type(input, 'av')
    expect(await screen.findByRole('option', { name: 'Aviador · stock' })).toBeTruthy()
    await userEvent.keyboard('{ArrowDown}{Enter}')

    expect(onSelect).toHaveBeenCalledWith(expect.objectContaining({ id: expect.any(Number) }))
    expect((input as HTMLInputElement).value).toBe('')
  })

  it('WHEN clicking an option THEN onSelect with that option', async () => {
    const onSelect = vi.fn()
    render(<Demo onSelect={onSelect} />)

    await userEvent.type(screen.getByRole('combobox', { name: 'Producto' }), 'cl')
    await userEvent.click(await screen.findByRole('option', { name: 'Clásico · stock' }))

    expect(onSelect).toHaveBeenCalledWith(ITEMS[1])
  })

  it('WHEN no results THEN empty message; with error THEN aria-invalid and associated help', async () => {
    render(<Demo onSelect={vi.fn()} items={[]} error="Elige un producto" />)

    const input = screen.getByRole('combobox', { name: 'Producto' })
    expect(input.getAttribute('aria-invalid')).toBe('true')
    expect(input.getAttribute('aria-describedby')).toContain('-hint')
    expect(screen.getByText('Elige un producto')).toBeTruthy()
    await userEvent.type(input, 'zz')
    expect(await screen.findByText('Sin resultados')).toBeTruthy()
  })

  it('WHEN an option is chosen THEN the search does not run again with its label [AC-6]', async () => {
    const onQuery = vi.fn()
    render(<Demo onSelect={vi.fn()} onQuery={onQuery} />)

    await userEvent.type(screen.getByRole('combobox', { name: 'Producto' }), 'cl')
    await userEvent.click(await screen.findByRole('option', { name: 'Clásico · stock' }))

    expect(onQuery).not.toHaveBeenCalledWith('Clásico')
    expect(onQuery).toHaveBeenLastCalledWith('')
  })

  it('WHEN the list closes with an outside click THEN the search text stays [AC-6]', async () => {
    const onQuery = vi.fn()
    render(<Demo onSelect={vi.fn()} onQuery={onQuery} />)

    const input = screen.getByRole('combobox', { name: 'Producto' })
    await userEvent.type(input, 'av')
    await screen.findByRole('option', { name: 'Aviador · stock' })
    await userEvent.click(document.body)
    await waitFor(() => expect(document.querySelector('[data-slot="combobox-content"]')).toBeNull())

    expect(onQuery).toHaveBeenLastCalledWith('av')
    expect((input as HTMLInputElement).value).toBe('av')
  })

  it('WHEN there are no items THEN no popup is mounted and the empty message is a live status [AC-6]', async () => {
    render(<Demo onSelect={vi.fn()} items={[]} />)

    await userEvent.type(screen.getByRole('combobox', { name: 'Producto' }), 'zz')

    expect(document.querySelector('[data-slot="combobox-content"]')).toBeNull()
    expect(await screen.findByRole('status')).toBeTruthy()
    expect(screen.getByRole('status').textContent).toBe('Sin resultados')
  })

  it('WHEN no help or error THEN the input has no description', () => {
    render(<Demo onSelect={vi.fn()} hint="" />)

    expect(screen.getByRole('combobox', { name: 'Producto' }).getAttribute('aria-describedby')).toBeNull()
  })

  it('AC-6: WHEN total=1, query="" and items.length=1 THEN shows UIFixedValue and calls onSelect once', () => {
    const onSelect = vi.fn()
    const { rerender } = render(<Demo onSelect={onSelect} items={[ITEMS[0]]} total={1} />)

    expect(screen.queryByRole('combobox')).toBeNull()
    expect(screen.getByRole('term').textContent).toBe('Producto')
    expect(screen.getByRole('definition').textContent).toBe('Aviador')
    expect(onSelect).toHaveBeenCalledTimes(1)
    expect(onSelect).toHaveBeenCalledWith(ITEMS[0])

    rerender(<Demo onSelect={onSelect} items={[ITEMS[0]]} total={1} />)
    expect(onSelect).toHaveBeenCalledTimes(1)
  })

  it('AC-6: WHEN total=2 THEN renders the normal combobox', () => {
    render(<Demo onSelect={vi.fn()} items={ITEMS} total={2} />)

    expect(screen.getByRole('combobox', { name: 'Producto' })).toBeDefined()
  })
})

const CHAPTERS: Item[] = [
  { id: 1, name: 'Aviador' },
  { id: 2, name: 'Clásico' },
  { id: 3, name: 'Aviadora' },
]

/** Capítulo A para los ítems 1 y 3, capítulo B para el 2. */
function byChapter(item: Item): { key: string; label: string } {
  return item.id === 2 ? { key: 'B', label: 'Capítulo B' } : { key: 'A', label: 'Capítulo A' }
}

/** Grupos dentro del listbox: el `Field` que envuelve el combobox también tiene `role="group"`. */
async function listGroups(): Promise<HTMLElement[]> {
  return within(await screen.findByRole('listbox')).queryAllByRole('group')
}

describe('UICombobox grouped results and load more [AC-31, AC-32]', () => {
  it('WHEN consecutive items share a group key THEN they share one header [AC-31]', async () => {
    render(<Demo onSelect={vi.fn()} items={[CHAPTERS[0], CHAPTERS[2], CHAPTERS[1]]} group={byChapter} />)

    await userEvent.type(screen.getByRole('combobox', { name: 'Producto' }), 'a')

    const groups = await listGroups()
    expect(groups).toHaveLength(2)
    expect(within(groups[0]).getByRole('option', { name: 'Aviador · stock' })).toBeTruthy()
    expect(within(groups[0]).getByRole('option', { name: 'Aviadora · stock' })).toBeTruthy()
    expect(screen.getByRole('group', { name: 'Capítulo B' })).toBeTruthy()
  })

  it('WHEN a key comes back after another group THEN it starts a new header [AC-31]', async () => {
    render(<Demo onSelect={vi.fn()} items={CHAPTERS} group={byChapter} />)

    await userEvent.type(screen.getByRole('combobox', { name: 'Producto' }), 'a')

    expect(await listGroups()).toHaveLength(3)
  })

  it('WHEN no group prop THEN no group is rendered', async () => {
    render(<Demo onSelect={vi.fn()} />)

    await userEvent.type(screen.getByRole('combobox', { name: 'Producto' }), 'av')
    await screen.findByRole('option', { name: 'Aviador · stock' })

    expect(await listGroups()).toHaveLength(0)
  })

  it('WHEN hasMore THEN the load more option calls onLoadMore not onSelect and keeps focus [AC-32]', async () => {
    const onSelect = vi.fn()
    const onLoadMore = vi.fn()
    render(<Demo onSelect={onSelect} onLoadMore={onLoadMore} hasMore />)

    const input = screen.getByRole('combobox', { name: 'Producto' })
    await userEvent.type(input, 'av')
    await userEvent.click(await screen.findByRole('option', { name: 'Cargar más' }))

    expect(onLoadMore).toHaveBeenCalledTimes(1)
    expect(onSelect).not.toHaveBeenCalled()
    expect(document.activeElement).toBe(input)
  })

  it('WHEN load more is chosen THEN the search text stays and the option label does not replace it [AC-32]', async () => {
    const onQuery = vi.fn()
    render(<Demo onSelect={vi.fn()} onQuery={onQuery} onLoadMore={vi.fn()} hasMore />)

    const input = screen.getByRole('combobox', { name: 'Producto' })
    await userEvent.type(input, 'av')
    await userEvent.click(await screen.findByRole('option', { name: 'Cargar más' }))

    expect(onQuery).toHaveBeenLastCalledWith('av')
    expect((input as HTMLInputElement).value).toBe('av')
  })

  it('WHEN the load more option is reached with the keyboard THEN Enter calls onLoadMore [AC-32]', async () => {
    const onSelect = vi.fn()
    const onLoadMore = vi.fn()
    render(<Demo onSelect={onSelect} onLoadMore={onLoadMore} hasMore />)

    await userEvent.type(screen.getByRole('combobox', { name: 'Producto' }), 'av')
    await screen.findByRole('option', { name: 'Cargar más' })
    await userEvent.keyboard('{ArrowDown}{ArrowDown}{Enter}')

    expect(onLoadMore).toHaveBeenCalledTimes(1)
    expect(onSelect).not.toHaveBeenCalled()
  })

  it('WHEN loading THEN the list is busy while the next page arrives [AC-32]', async () => {
    render(<Demo onSelect={vi.fn()} loading />)

    await userEvent.type(screen.getByRole('combobox', { name: 'Producto' }), 'av')

    expect((await screen.findByRole('listbox')).getAttribute('aria-busy')).toBe('true')
  })

  it('WHEN group and hasMore THEN the load more option is not inside any group [AC-32]', async () => {
    render(<Demo onSelect={vi.fn()} group={byChapter} hasMore onLoadMore={vi.fn()} />)

    await userEvent.type(screen.getByRole('combobox', { name: 'Producto' }), 'av')

    const loadMore = await screen.findByRole('option', { name: 'Cargar más' })
    expect(loadMore.closest('[data-slot="combobox-group"]')).toBeNull()
  })
})

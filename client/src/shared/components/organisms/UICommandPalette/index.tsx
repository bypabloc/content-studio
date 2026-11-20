import { useMemo, useState, type KeyboardEvent } from 'react'

import { UIBox } from '../../atoms/UIBox'
import { type IconName, UIIcon } from '../../atoms/UIIcon'
import { Input } from '../../shadcn/input'
import { useShortcut } from '@/shared/hooks/useShortcut'

/** Una sección a la que se puede ir: `id` es lo que recibe `onSelect`; `label`, lo que se busca y se muestra; `icon`, el que la precede (spec 009, D-5). */
export type CommandItem = { id: string; label: string; icon?: IconName }

/** Textos que llegan por props, como en el resto de los organismos (spec 008, D-3). */
type Labels = { title: string; placeholder: string; empty: string }

type Props = { items: readonly CommandItem[]; onSelect: (id: string) => void; labels: Labels }

/** Sin tildes ni mayúsculas, para que una búsqueda sin acento encuentre la sección. */
function fold(text: string): string {
  return text.normalize('NFD').replace(/\p{Diacritic}/gu, '').toLowerCase()
}

/**
 * Paleta de comandos (Ctrl+K): escribir filtra las secciones sin distinguir tildes, las flechas eligen y Enter o un
 * clic llaman a `onSelect` con el id de la sección. Los ítems llegan por props (spec 008, D-3): la pantalla decide a
 * dónde lleva cada uno.
 *
 * @author Pablo Contreras
 * @since 2026/11/19
 */
export function UICommandPalette({ items, onSelect, labels }: Props): React.JSX.Element | null {
  const [open, setOpen] = useState(false)
  const [query, setQuery] = useState('')
  const [cursor, setCursor] = useState(0)

  useShortcut('mod+k', () => setOpen(true))

  const matches = useMemo(() => items.filter((item) => fold(item.label).includes(fold(query))), [items, query])

  const close = () => {
    setOpen(false)
    setQuery('')
    setCursor(0)
  }

  const choose = (item: CommandItem) => {
    onSelect(item.id)
    close()
  }

  const onKeyDown = (event: KeyboardEvent) => {
    if (event.key === 'Escape') close()
    if (event.key === 'ArrowDown') setCursor((index) => Math.min(index + 1, matches.length - 1))
    if (event.key === 'ArrowUp') setCursor((index) => Math.max(index - 1, 0))
    const chosen = matches[cursor]
    if (event.key === 'Enter' && chosen) choose(chosen)
  }

  if (!open) return null

  return (
    <UIBox
      role="dialog"
      aria-label={labels.title}
      onKeyDown={onKeyDown}
      className="fixed inset-0 z-50 flex items-start justify-center bg-black/40 pt-24"
    >
      <UIBox className="w-full max-w-md rounded-lg border border-border bg-card p-2 shadow-lg">
        <Input
          role="combobox"
          aria-expanded="true"
          aria-controls="palette-list"
          aria-autocomplete="list"
          autoFocus
          value={query}
          placeholder={labels.placeholder}
          onChange={(event) => {
            setQuery(event.target.value)
            setCursor(0)
          }}
          className="w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-ring"
        />
        <UIBox role="listbox" id="palette-list" className="mt-2 flex flex-col">
          {matches.length === 0 ? (
            <UIBox className="px-3 py-2 text-sm text-muted-foreground">{labels.empty}</UIBox>
          ) : (
            matches.map((item, index) => (
              <UIBox
                key={item.id}
                role="option"
                aria-selected={index === cursor}
                onClick={() => choose(item)}
                className={`flex cursor-pointer items-center gap-2 rounded-md px-3 py-2 text-sm ${index === cursor ? 'bg-accent' : ''}`}
              >
                {item.icon ? <UIIcon name={item.icon} className="size-4" /> : null}
                {item.label}
              </UIBox>
            ))
          )}
        </UIBox>
      </UIBox>
    </UIBox>
  )
}

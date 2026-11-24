import { cn } from 'cn'
import { Fragment, type ReactNode, useEffect, useId, useRef, useState } from 'react'

import {
  Combobox,
  ComboboxCollection,
  ComboboxContent,
  ComboboxGroup,
  ComboboxInput,
  ComboboxItem,
  ComboboxLabel,
  ComboboxList,
} from '../../shadcn/combobox'
import { UIFieldFrame } from '../../atoms/UIFieldFrame'

import { UIFixedValue } from '../../atoms/UIFixedValue'
import { UIIcon } from '../../atoms/UIIcon'
import { UIBox } from '../../atoms/UIBox'

type Props<T> = {
  label: string
  placeholder?: string
  items: T[]
  itemKey: (item: T) => string | number
  itemLabel: (item: T) => string
  renderItem: (item: T) => ReactNode
  /** Ítems visibles pero no elegibles (p. ej. sin stock). */
  isItemDisabled?: (item: T) => boolean
  onSelect: (item: T) => void
  query: string
  onQueryChange: (query: string) => void
  empty: string
  hint?: ReactNode
  error?: string
  total?: number
  /** Encabezado del grupo de cada ítem; ítems consecutivos con la misma `key` comparten encabezado. */
  group?: (item: T) => { key: string; label: string }
  /** Hay más páginas: muestra al final de la lista «Cargar más», que llama `onLoadMore` y no elige nada. */
  hasMore?: boolean
  onLoadMore?: () => void
  /** Texto de la opción «Cargar más» (obligatorio con `hasMore`). */
  loadMoreLabel?: string
  /** Marca la lista como ocupada (`aria-busy`) mientras llega la página siguiente. */
  loading?: boolean
}

/** Opción centinela «Cargar más»: no es un dato, así que se reconoce por identidad. */
type LoadMore = { readonly kind: 'load-more' }
const LOAD_MORE: LoadMore = { kind: 'load-more' }
const LOAD_MORE_VALUE = 'load-more'

/** Ítem de la lista: un dato o la opción «Cargar más». */
type Entry<T> = T | LoadMore

/** Tramo de la lista: un grupo con encabezado o, sin `label`, ítems sueltos (la opción «Cargar más»). */
type Section<T> = { value: string; label?: string; items: Entry<T>[] }

const OPTION_CLASS =
  'ui-typography-body min-h-11 cursor-pointer px-3 text-foreground data-highlighted:bg-accent data-highlighted:text-accent-foreground'

function isLoadMore<T>(entry: Entry<T>): entry is LoadMore {
  return entry === LOAD_MORE
}

/** Parte los ítems en grupos: consecutivos con la misma `key` comparten encabezado, en orden de llegada. */
function sectionsOf<T>(items: readonly T[], group: (item: T) => { key: string; label: string }): Section<T>[] {
  const sections: Section<T>[] = []
  let previousKey: string | undefined
  for (const item of items) {
    const { key, label } = group(item)
    if (key !== previousKey) {
      sections.push({ value: `${sections.length}:${key}`, label, items: [] })
      previousKey = key
    }
    sections[sections.length - 1].items.push(item)
  }
  return sections
}

/**
 * Buscador con resultados (combobox): el texto llega filtrado del server
 * (`items`), las flechas recorren los resultados, Enter elige y Escape
 * cierra. Elegir llama a `onSelect` y limpia el texto: sirve para agregar
 * ítems a una lista. `isItemDisabled` deja ver un ítem sin permitir elegirlo. Label visible, ayuda y error asociados.
 * Sin ítems no monta el popup (un popup vacío oculta el resto del diálogo): si ya hay
 * texto escrito, `empty` aparece bajo el campo como estado vivo. Con `open` controlado, el input nunca queda expandido sin lista.
 * Opción única: con total === 1, query === '' e items.length === 1 muestra UIFixedValue
 * y notifica onSelect(items[0]) exactamente una vez.
 * Con `group` agrupa los resultados por encabezado; con `hasMore` añade al final «Cargar más»,
 * que llama a `onLoadMore` y no elige nada; con `loading` marca la lista como ocupada.
 *
 * @author Pablo Contreras
 * @since 2026/09/28
 * @since 2026/11/19
 */
export function UICombobox<T>({
  label,
  placeholder,
  items,
  itemKey,
  itemLabel,
  renderItem,
  isItemDisabled,
  onSelect,
  query,
  onQueryChange,
  empty,
  hint,
  error,
  total,
  group,
  hasMore = false,
  onLoadMore,
  loadMoreLabel,
  loading = false,
}: Props<T>): React.JSX.Element {
  const inputId = useId()
  const errorId = `${inputId}-error`
  const hintId = `${inputId}-hint`
  const describedBy = [error ? errorId : null, hint ? hintId : null].filter(Boolean).join(' ') || undefined

  const isSingle = total === 1 && query === '' && items.length === 1
  const singleItem = isSingle ? items[0] : undefined
  const showEmpty = items.length === 0 && query.trim() !== ''
  const notifiedRef = useRef(false)
  const [open, setOpen] = useState(false)

  useEffect(() => {
    if (isSingle && singleItem !== undefined && !notifiedRef.current) {
      notifiedRef.current = true
      onSelect(singleItem)
    }
  }, [isSingle, singleItem, onSelect])

  if (isSingle && singleItem !== undefined) {
    return <UIFixedValue label={label} value={itemLabel(singleItem)} />
  }

  const sections = group ? sectionsOf(items, group) : undefined
  const loadMoreSection: Section<T> = { value: LOAD_MORE_VALUE, items: [LOAD_MORE] }
  const rootItems = sections
    ? [...sections, ...(hasMore ? [loadMoreSection] : [])]
    : [...items, ...(hasMore ? [LOAD_MORE] : [])]

  function renderEntry(entry: Entry<T>): React.JSX.Element {
    if (isLoadMore(entry)) {
      return (
        <ComboboxItem key={LOAD_MORE_VALUE} value={LOAD_MORE} className={cn(OPTION_CLASS, 'font-bold text-primary')}>
          {loadMoreLabel}
        </ComboboxItem>
      )
    }
    return (
      <ComboboxItem key={itemKey(entry)} value={entry} disabled={isItemDisabled?.(entry)} className={OPTION_CLASS}>
        {renderItem(entry)}
      </ComboboxItem>
    )
  }

  function renderSection(section: Section<T>): React.JSX.Element {
    if (section.label === undefined) {
      return <Fragment key={section.value}>{section.items.map(renderEntry)}</Fragment>
    }
    return (
      <ComboboxGroup key={section.value} items={section.items}>
        <ComboboxLabel>{section.label}</ComboboxLabel>
        <ComboboxCollection>{renderEntry}</ComboboxCollection>
      </ComboboxGroup>
    )
  }

  return (
    <UIFieldFrame label={label} htmlFor={inputId} error={error} errorId={errorId} hint={hint} hintId={hintId}>
      <Combobox<Entry<T>>
        items={rootItems}
        filter={null}
        value={null}
        open={open && items.length > 0}
        onOpenChange={(next) => setOpen(next)}
        inputValue={query}
        onInputValueChange={(text, details) => {
          // Solo lo que escribe la persona es búsqueda: Base UI escribe el label al elegir y vacía el texto al cerrar la lista.
          if (details.reason !== 'input-change') return
          onQueryChange(text)
        }}
        onValueChange={(entry) => {
          if (entry === null) return
          if (isLoadMore(entry)) {
            onLoadMore?.()
            return
          }
          onSelect(entry)
          onQueryChange('')
        }}
        itemToStringLabel={(entry) => (isLoadMore(entry) ? (loadMoreLabel ?? '') : itemLabel(entry))}
        autoHighlight
      >
        <UIBox className="relative">
          <UIBox as="span" className="pointer-events-none absolute inset-y-0 left-3.5 flex items-center text-muted-foreground">
            <UIIcon name="search" />
          </UIBox>
          <ComboboxInput
            id={inputId}
            placeholder={placeholder}
            aria-invalid={error ? true : undefined}
            aria-describedby={describedBy}
            className={cn(
              'ui-typography-body h-auto min-h-12 rounded-xl bg-card pl-11 text-base text-foreground hover:border-foreground-secondary focus-visible:border-ring focus-visible:ring-4 focus-visible:ring-ring/20 md:text-base dark:bg-card',
              error ? 'border-destructive' : 'border-input',
            )}
          />
        </UIBox>
        {items.length ? (
          <ComboboxContent className="bg-card text-foreground">
            <ComboboxList aria-busy={loading || undefined}>
              {sections ? (section: Section<T>) => renderSection(section) : (entry: Entry<T>) => renderEntry(entry)}
            </ComboboxList>
          </ComboboxContent>
        ) : null}
      </Combobox>
      {showEmpty ? <UIBox role="status" className="ui-typography-body text-muted-foreground">{empty}</UIBox> : null}
    </UIFieldFrame>
  )
}

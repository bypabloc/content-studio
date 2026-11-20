import { useMemo, useState, type KeyboardEvent } from 'react';
import { useShortcut } from '@/shared/hooks/useShortcut';
import { t } from '@/shared/i18n/t';
import { navItems, type NavItem } from './nav';

/** Sin tildes ni mayúsculas, para que una búsqueda sin acento encuentre la sección. */
function fold(text: string): string {
  return text.normalize('NFD').replace(/\p{Diacritic}/gu, '').toLowerCase();
}

/** Ctrl+K abre la paleta: escribir filtra las secciones, las flechas eligen y Enter va a la sección. */
export function CommandPalette({ items = navItems() }: { items?: readonly NavItem[] }) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [cursor, setCursor] = useState(0);

  useShortcut('mod+k', () => setOpen(true));

  const matches = useMemo(
    () => items.filter((item) => fold(item.label).includes(fold(query))),
    [items, query],
  );

  const close = () => {
    setOpen(false);
    setQuery('');
    setCursor(0);
  };

  const go = (item: NavItem) => {
    window.location.hash = `#/${item.id}`;
    close();
  };

  const onKeyDown = (event: KeyboardEvent) => {
    if (event.key === 'Escape') close();
    if (event.key === 'ArrowDown') setCursor((index) => Math.min(index + 1, matches.length - 1));
    if (event.key === 'ArrowUp') setCursor((index) => Math.max(index - 1, 0));
    const chosen = matches[cursor];
    if (event.key === 'Enter' && chosen) go(chosen);
  };

  if (!open) return null;

  return (
    <div
      role="dialog"
      aria-label={t('palette.title')}
      onKeyDown={onKeyDown}
      className="fixed inset-0 z-50 flex items-start justify-center bg-black/40 pt-24"
    >
      <div className="w-full max-w-md rounded-lg border border-border bg-card p-2 shadow-lg">
        <input
          role="combobox"
          aria-expanded="true"
          aria-controls="palette-list"
          aria-autocomplete="list"
          autoFocus
          value={query}
          placeholder={t('palette.placeholder')}
          onChange={(event) => {
            setQuery(event.target.value);
            setCursor(0);
          }}
          className="w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-ring"
        />
        <ul id="palette-list" role="listbox" className="mt-2 flex flex-col">
          {matches.length === 0 ? (
            <li className="px-3 py-2 text-sm text-muted-foreground">{t('palette.empty')}</li>
          ) : (
            matches.map((item, index) => (
              <li
                key={item.id}
                role="option"
                aria-selected={index === cursor}
                onClick={() => go(item)}
                className={`cursor-pointer rounded-md px-3 py-2 text-sm ${index === cursor ? 'bg-accent' : ''}`}
              >
                {item.label}
              </li>
            ))
          )}
        </ul>
      </div>
    </div>
  );
}

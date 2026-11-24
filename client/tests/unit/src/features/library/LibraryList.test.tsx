import { cleanup, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { LibraryList } from '@/features/library/LibraryList';
import { t } from '@/shared/i18n/t';

import { libraryItem } from './fixtures';

afterEach(() => cleanup());

describe('LibraryList (spec 020, D-6 y AC-9)', () => {
  beforeEach(() => vi.clearAllMocks());

  it('AC-9: con 5.000 ítems solo unas cien filas están en el DOM', () => {
    const items = Array.from({ length: 5000 }, (_, index) => libraryItem({ id: index + 1, name: `pista-${index}.wav` }));

    render(<LibraryList items={items} onOpen={vi.fn()} selected={[]} onSelect={vi.fn()} />);

    const rows = screen.getAllByRole('listitem');
    expect(rows.length).toBeGreaterThan(0);
    expect(rows.length).toBeLessThanOrEqual(100);
  });

  it('cada fila trae tipo, duración, tamaño, fecha y origen; selecciona y abre', async () => {
    const onOpen = vi.fn();
    const onSelect = vi.fn();
    const { rerender } = render(
      <LibraryList items={[libraryItem(), libraryItem({ id: 2, name: 'v.mp4', origin: 'watched' })]} onOpen={onOpen} selected={[]} onSelect={onSelect} />,
    );

    expect(screen.getAllByText(t('library.kind.narration'))).toHaveLength(2);
    expect(screen.getByText(t('library.origin.watched'))).toBeTruthy();
    expect(screen.getAllByText('2 KB')).toHaveLength(2);
    await userEvent.click(screen.getByRole('checkbox', { name: t('library.select', { name: 'v.mp4' }) }));
    await userEvent.click(screen.getByRole('button', { name: 'take.wav' }));
    expect(onSelect).toHaveBeenCalledWith([2]);
    expect(onOpen).toHaveBeenCalledWith(1);

    rerender(<LibraryList items={[libraryItem()]} onOpen={onOpen} selected={[1]} onSelect={onSelect} />);
    await userEvent.click(screen.getByRole('checkbox', { name: t('library.select', { name: 'take.wav' }) }));
    expect(onSelect).toHaveBeenLastCalledWith([]);
  });
});

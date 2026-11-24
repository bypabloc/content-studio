import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { LibraryToolbar } from '@/features/library/LibraryToolbar';
import { EMPTY_FILTERS } from '@/features/library/query';
import { t } from '@/shared/i18n/t';

afterEach(() => cleanup());

function renderToolbar(onChange = vi.fn(), onView = vi.fn(), onRefresh = vi.fn()) {
  render(
    <LibraryToolbar filters={EMPTY_FILTERS} onChange={onChange} tags={[{ name: 'reel', count: 1 }]} view="grid" onView={onView} scanning={false} onRefresh={onRefresh} />,
  );
  return { onChange, onView, onRefresh };
}

describe('LibraryToolbar (spec 020, D-6)', () => {
  beforeEach(() => vi.clearAllMocks());

  it('la búsqueda, el contenido y la ★ cambian los filtros', async () => {
    const { onChange } = renderToolbar();

    fireEvent.change(screen.getByRole('searchbox', { name: t('library.search') }), { target: { value: 'acta' } });
    await userEvent.click(screen.getByRole('switch', { name: t('library.search.content') }));
    await userEvent.click(screen.getByRole('switch', { name: t('library.filter.starred') }));

    expect(onChange).toHaveBeenCalledWith(expect.objectContaining({ q: 'acta' }));
    expect(onChange).toHaveBeenCalledWith(expect.objectContaining({ content: true }));
    expect(onChange).toHaveBeenCalledWith(expect.objectContaining({ starred: true }));
  });

  it('los selectores eligen tipo, medio, fecha, duración, etiqueta y orden; «cualquiera» vacía el filtro', async () => {
    const { onChange } = renderToolbar();
    const pick = async (combo: string, option: string) => {
      await userEvent.click(await screen.findByRole('combobox', { name: combo }));
      await userEvent.click(await screen.findByRole('option', { name: option }));
    };

    await pick(t('library.filter.media'), t('library.media.video'));
    await pick(t('library.filter.date'), t('library.date.week'));
    await pick(t('library.filter.length'), t('library.length.long'));
    await pick(t('library.filter.tag'), 'reel');
    await pick(t('library.sort'), t('library.sort.size'));
    await pick(t('library.filter.media'), t('library.filter.any'));

    expect(onChange).toHaveBeenCalledWith(expect.objectContaining({ mediaType: 'video' }));
    expect(onChange).toHaveBeenCalledWith(expect.objectContaining({ since: 'week' }));
    expect(onChange).toHaveBeenCalledWith(expect.objectContaining({ length: 'long' }));
    expect(onChange).toHaveBeenCalledWith(expect.objectContaining({ tag: 'reel' }));
    expect(onChange).toHaveBeenCalledWith(expect.objectContaining({ sort: 'size' }));
    expect(onChange).toHaveBeenLastCalledWith(expect.objectContaining({ mediaType: '' }));
  });

  it('el tipo usa los nombres del catálogo', async () => {
    const { onChange } = renderToolbar();

    await userEvent.click(await screen.findByRole('combobox', { name: t('library.filter.kind') }));
    await userEvent.click(await screen.findByRole('option', { name: t('library.kind.music') }));

    expect(onChange).toHaveBeenCalledWith(expect.objectContaining({ kind: 'music' }));
  });

  it('la vista y «Actualizar» avisan', async () => {
    const { onView, onRefresh } = renderToolbar();

    await userEvent.click(screen.getByRole('button', { name: t('library.view.list') }));
    await userEvent.click(screen.getByRole('button', { name: t('library.view.grid') }));
    await userEvent.click(screen.getByRole('button', { name: t('library.refresh') }));

    expect(onView.mock.calls).toEqual([['list'], ['grid']]);
    expect(onRefresh).toHaveBeenCalledTimes(1);
  });
});

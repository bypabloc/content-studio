import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { ItemOrganize } from '@/features/library/ItemOrganize';
import { t } from '@/shared/i18n/t';

import { libraryItem } from './fixtures';

const { api, open, openPath } = vi.hoisted(() => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    del: vi.fn(),
    patch: vi.fn(),
    fileUrl: (path: string) => `file://${path}`,
    queryUrl: (path: string) => `http://api${path}`,
  },
  open: vi.fn(),
  openPath: vi.fn(),
}));
vi.mock('@/shared/api/context', () => ({ useApi: () => api }));
vi.mock('@tauri-apps/plugin-dialog', () => ({ open }));
vi.mock('@tauri-apps/plugin-opener', () => ({ openPath }));

const wrap = (ui: React.ReactNode) =>
  render(<QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>{ui}</QueryClientProvider>);

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
  window.location.hash = '';
});

describe('ItemOrganize (spec 020, D-3)', () => {
  beforeEach(() => {
    api.get.mockResolvedValue([{ id: 2, name: 'Curso', count: 0 }]);
    api.post.mockResolvedValue([]);
    api.del.mockResolvedValue([]);
  });

  it('etiqueta, quita una etiqueta y agrega a un proyecto', async () => {
    wrap(<ItemOrganize item={libraryItem({ tags: ['viejo'] })} />);

    fireEvent.change(screen.getByRole('textbox', { name: t('library.tags.new') }), { target: { value: 'reel 12' } });
    await userEvent.click(screen.getByRole('button', { name: t('library.tags.add') }));
    await userEvent.click(screen.getByRole('button', { name: t('library.tags.remove', { name: 'viejo' }) }));
    await userEvent.click(await screen.findByRole('combobox', { name: t('library.projects.add') }));
    await userEvent.click(await screen.findByRole('option', { name: 'Curso' }));

    await waitFor(() => expect(api.post).toHaveBeenCalledWith('/library/1/tags', { name: 'reel 12' }));
    expect(api.del).toHaveBeenCalledWith('/library/1/tags?name=viejo');
    await waitFor(() => expect(api.post).toHaveBeenCalledWith('/projects/2/items', { items: [1] }));
  });

  it('sin proyectos no muestra el selector; un error se avisa', async () => {
    api.get.mockResolvedValue([]);
    api.post.mockRejectedValue(new Error('no'));
    wrap(<ItemOrganize item={libraryItem()} />);

    fireEvent.change(screen.getByRole('textbox', { name: t('library.tags.new') }), { target: { value: 'x' } });
    await userEvent.click(screen.getByRole('button', { name: t('library.tags.add') }));

    await waitFor(() => expect(api.post).toHaveBeenCalled());
    expect(screen.queryByRole('combobox', { name: t('library.projects.add') })).toBeNull();
  });
});

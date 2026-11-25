import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { LibraryPage } from '@/features/library/LibraryPage';
import { t } from '@/shared/i18n/t';
import { setPrefill } from '@/shared/navigation/prefill';

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

const items = [libraryItem(), libraryItem({ id: 2, name: 'clip.mp4', media_type: 'video' })];

function serve(total = 2) {
  api.get.mockImplementation(async (path: string) => {
    if (path.startsWith('/library?')) return { items: total ? items : [], total };
    if (path === '/library/1') return { item: items[0], job: null, outputs: [], takes: [] };
    if (path === '/library/storage') return { by_kind: [], heaviest: [], unchosen: [], outputs: { path: 'D:/out', size: 0 }, folders: [] };
    if (path === '/settings/library.last_scan') return { value: new Date().toISOString() };
    if (path === '/settings/library.view') return { value: null };
    if (path.startsWith('/media/peaks')) return { peaks: [0.5] };
    return [];
  });
  api.put.mockImplementation(async (_path: string, body: { value: unknown }) => ({ key: 'library.view', value: body.value }));
  api.post.mockResolvedValue({ removed: 1 });
}

describe('LibraryPage (spec 020, D-6)', () => {
  beforeEach(() => serve());

  it('muestra la grilla con la cantidad, y abre el detalle de un ítem', async () => {
    wrap(<LibraryPage />);

    expect(await screen.findByText(t('library.count', { count: 2 }))).toBeTruthy();
    await userEvent.click(await screen.findByRole('button', { name: t('library.open', { name: 'take.wav' }) }));
    expect(await screen.findByRole('dialog', { name: 'take.wav' })).toBeTruthy();
    await userEvent.click(screen.getByRole('button', { name: t('ui.dialog.close') }));
  });

  it('la lista manda los seleccionados a la papelera con una confirmación', async () => {
    wrap(<LibraryPage />);

    await userEvent.click(screen.getByRole('button', { name: t('library.view.list') }));
    await userEvent.click(await screen.findByRole('checkbox', { name: t('library.select', { name: 'clip.mp4' }) }));
    await userEvent.click(screen.getByRole('button', { name: t('library.trash') }));
    await userEvent.click(screen.getAllByRole('button', { name: t('library.trash') }).at(-1) as HTMLElement);

    await waitFor(() => expect(api.post).toHaveBeenCalledWith('/library/trash', { items: [2] }));
  });

  it('sin resultados muestra el vacío; «Espacio» cambia la vista; un filtro vuelve a la página 1', async () => {
    serve(0);
    wrap(<LibraryPage />);

    expect(await screen.findByText(t('library.empty'))).toBeTruthy();
    fireEvent.change(screen.getByRole('searchbox', { name: t('library.search') }), { target: { value: 'x' } });
    await waitFor(() => expect(api.get).toHaveBeenCalledWith(expect.stringContaining('q=x')));
    await userEvent.click(screen.getByRole('button', { name: t('library.scope.storage') }));
    expect(await screen.findByText(t('library.storage.total', { size: '0 B', path: 'D:/out' }))).toBeTruthy();
  });

  it('con más de una página muestra la paginación', async () => {
    api.get.mockImplementation(async (path: string) =>
      path.startsWith('/library?') ? { items, total: 450 } : path.startsWith('/settings/') ? { value: new Date().toISOString() } : [],
    );
    wrap(<LibraryPage />);

    await userEvent.click(await screen.findByRole('button', { name: t('library.pages.next') }));
    await waitFor(() => expect(api.get).toHaveBeenCalledWith(expect.stringContaining('page=2')));
  });
});

describe('LibraryPage con un enlace (spec 031, AC-2)', () => {
  it('WHEN llega library/<id> THEN pide ese elemento para abrir su detalle', async () => {
    serve();
    setPrefill('library', { id: '1' });
    wrap(<LibraryPage />);
    await waitFor(() => expect(api.get).toHaveBeenCalledWith('/library/1'));
  });

  it('WHEN llega job/<id> THEN pide el trabajo a la API', async () => {
    serve();
    setPrefill('library', { job: '42' });
    wrap(<LibraryPage />);
    await waitFor(() => expect(api.get).toHaveBeenCalledWith('/jobs/42'));
  });
});

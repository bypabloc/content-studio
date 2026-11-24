import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { cleanup, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { StorageView } from '@/features/library/StorageView';
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

describe('StorageView (spec 020, D-5)', () => {
  it('muestra los totales y manda a la papelera lo elegido con una sola confirmación', async () => {
    api.get.mockResolvedValue({
      by_kind: [{ kind: 'music', size: 2048, count: 1 }],
      heaviest: [libraryItem({ id: 7, path: 'D:/out/a/grande.wav', size: 4096 })],
      unchosen: [],
      outputs: { path: 'D:/out', size: 4096 },
      folders: [{ id: 1, path: 'D:/videos', name: 'videos', size: 10 }],
    });
    api.post.mockResolvedValue({ removed: 1 });
    wrap(<StorageView />);

    expect(await screen.findByText(t('library.storage.total', { size: '4 KB', path: 'D:/out' }))).toBeTruthy();
    expect(screen.getByText(t('library.storage.folder', { name: 'videos', size: '10 B' }))).toBeTruthy();
    expect(screen.getAllByText(t('library.storage.empty'))).toHaveLength(1);
    await userEvent.click(screen.getByRole('checkbox', { name: t('library.storage.row', { name: 'grande.wav', size: '4 KB' }) }));
    await userEvent.click(screen.getByRole('button', { name: t('library.trash') }));
    expect(await screen.findByText(t('library.trash.confirm', { count: 1, size: '4 KB' }))).toBeTruthy();
    await userEvent.click(screen.getAllByRole('button', { name: t('library.trash') }).at(-1) as HTMLElement);

    await waitFor(() => expect(api.post).toHaveBeenCalledWith('/library/trash', { items: [7] }));
  });

  it('un error al mandar a la papelera se avisa; desmarcar quita la selección', async () => {
    api.get.mockResolvedValue({
      by_kind: [],
      heaviest: [],
      unchosen: [libraryItem({ id: 8, path: 'D:/out/b/toma.wav' })],
      outputs: { path: 'D:/out', size: 0 },
      folders: [],
    });
    api.post.mockRejectedValue(new Error('protegido'));
    wrap(<StorageView />);

    const row = await screen.findByRole('checkbox', { name: t('library.storage.row', { name: 'toma.wav', size: '2 KB' }) });
    await userEvent.click(row);
    await userEvent.click(row);
    expect(screen.queryByRole('button', { name: t('library.trash') })).toBeNull();
    await userEvent.click(row);
    await userEvent.click(screen.getByRole('button', { name: t('library.trash') }));
    await userEvent.click(screen.getAllByRole('button', { name: t('library.trash') }).at(-1) as HTMLElement);
    await waitFor(() => expect(api.post).toHaveBeenCalled());
  });
});

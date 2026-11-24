import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { cleanup, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { ItemOrigin } from '@/features/library/ItemOrigin';
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

describe('ItemOrigin (spec 020, D-4)', () => {
  it('muestra los parámetros, repite y abre las otras salidas y tomas', async () => {
    api.post.mockResolvedValue({ id: 11 });
    const onOpen = vi.fn();
    wrap(<ItemOrigin detail={{
  item: libraryItem(),
  job: { id: 10, kind: 'narration', params: { text: 'hola', seed: 3 }, created_at: 'x', elapsed: 12.4 },
  outputs: [libraryItem({ id: 5, path: 'D:/out/a/take.srt', media_type: 'subtitle' })],
  takes: [{ ...libraryItem({ id: 6, path: 'D:/out/b/take.wav' }), starred: true }],
}} onOpen={onOpen} onClose={vi.fn()} />);

    expect(screen.getByText('hola')).toBeTruthy();
    expect(screen.getByText(t('library.origin.job_line', { id: 10, kind: 'narration', seconds: 12 }))).toBeTruthy();
    await userEvent.click(screen.getByRole('button', { name: t('library.repeat') }));
    await userEvent.click(screen.getByRole('button', { name: 'take.srt' }));
    await userEvent.click(screen.getByRole('button', { name: 'take.wav' }));

    await waitFor(() => expect(api.post).toHaveBeenCalledWith('/library/1/repeat'));
    expect(onOpen.mock.calls).toEqual([[5], [6]]);
  });

  it('«Editar y repetir» cierra y abre la sección con from_job', async () => {
    const onClose = vi.fn();
    wrap(<ItemOrigin detail={{
  item: libraryItem(),
  job: { id: 10, kind: 'narration', params: { text: 'hola', seed: 3 }, created_at: 'x', elapsed: 12.4 },
  outputs: [libraryItem({ id: 5, path: 'D:/out/a/take.srt', media_type: 'subtitle' })],
  takes: [{ ...libraryItem({ id: 6, path: 'D:/out/b/take.wav' }), starred: true }],
}} onOpen={vi.fn()} onClose={onClose} />);

    await userEvent.click(screen.getByRole('button', { name: t('library.edit_repeat') }));

    expect(onClose).toHaveBeenCalled();
    expect(window.location.hash).toBe('#/narration?from_job=10');
  });

  it('sin trabajo lo dice; un tipo sin sección no ofrece «Editar y repetir»; un error se avisa', async () => {
    const { unmount } = wrap(<ItemOrigin detail={{
  item: libraryItem(),
  job: null,
  outputs: [],
  takes: [],
}} onOpen={vi.fn()} onClose={vi.fn()} />);
    expect(screen.getByText(t('library.origin.none'))).toBeTruthy();
    unmount();

    api.post.mockRejectedValue(new Error('no'));
    wrap(<ItemOrigin detail={{
  item: libraryItem({ kind: 'trim' }),
  job: { id: 3, kind: 'media.trim', params: { start: 1 }, created_at: 'x', elapsed: null },
  outputs: [],
  takes: [],
}} onOpen={vi.fn()} onClose={vi.fn()} />);
    expect(screen.queryByRole('button', { name: t('library.edit_repeat') })).toBeNull();
    expect(screen.getByText('1')).toBeTruthy();
    await userEvent.click(screen.getByRole('button', { name: t('library.repeat') }));
    await waitFor(() => expect(api.post).toHaveBeenCalled());
  });
});

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { cleanup, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { LibraryGrid } from '@/features/library/LibraryGrid';
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

describe('LibraryGrid (spec 020, D-6)', () => {
  beforeEach(() => api.get.mockResolvedValue({ peaks: [0.2, 0.8] }));

  it('cada tarjeta trae miniatura, nombre, tipo, duración, ★, faltante y etiquetas; abrirla avisa', async () => {
    const onOpen = vi.fn();
    wrap(
      <LibraryGrid
        onOpen={onOpen}
        items={[
          libraryItem({ starred: true, tags: ['reel'] }),
          libraryItem({ id: 2, name: 'clip.mp4', media_type: 'video', kind: 'convert', missing: true }),
          libraryItem({ id: 3, name: 'a.srt', media_type: 'subtitle', duration: null }),
        ]}
      />,
    );

    expect(screen.getByRole('img', { name: t('library.thumb', { name: 'take.wav' }) })).toBeTruthy();
    expect(screen.getByRole('img', { name: t('library.thumb', { name: 'clip.mp4' }) }).getAttribute('src')).toBe('http://api/library/thumb/2');
    expect(screen.getByText(t('library.starred'))).toBeTruthy();
    expect(screen.getByText(t('library.missing'))).toBeTruthy();
    expect(screen.getByText('reel')).toBeTruthy();
    expect(screen.getAllByText('1:15')).toHaveLength(2);
    await userEvent.click(screen.getByRole('button', { name: t('library.open', { name: 'clip.mp4' }) }));
    expect(onOpen).toHaveBeenCalledWith(2);
    await waitFor(() => expect(api.get).toHaveBeenCalledWith('/media/peaks?path=D%3A%2Fout%2Fnarration%2Fa%2Ftake.wav&n=200'));
  });
});

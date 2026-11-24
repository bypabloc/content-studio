import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { cleanup, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { ItemDetail } from '@/features/library/ItemDetail';
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

function serve(item: ReturnType<typeof libraryItem>) {
  api.get.mockImplementation(async (path: string) => {
    if (path.startsWith('/library/')) return { item, job: null, outputs: [], takes: [] };
    if (path.startsWith('/media/peaks')) return { peaks: [0.1, 0.4] };
    return [];
  });
}

describe('ItemDetail (spec 020, D-6)', () => {
  it('muestra el reproductor del audio, los metadatos, el origen y las acciones', async () => {
    serve(libraryItem());
    wrap(<ItemDetail id={1} onOpen={vi.fn()} onClose={vi.fn()} />);

    expect(await screen.findByRole('dialog', { name: 'take.wav' })).toBeTruthy();
    expect(screen.getByText('D:/out/narration/a/take.wav')).toBeTruthy();
    expect(screen.getByText(t('library.origin.none'))).toBeTruthy();
    await waitFor(() => expect(api.get).toHaveBeenCalledWith(expect.stringMatching(/^\/media\/peaks/)));
  });

  it('un video usa los controles del sistema; cerrar avisa', async () => {
    serve(libraryItem({ name: 'clip.mp4', path: 'D:/v/clip.mp4', media_type: 'video' }));
    const onClose = vi.fn();
    wrap(<ItemDetail id={2} onOpen={vi.fn()} onClose={onClose} />);

    await screen.findByRole('dialog', { name: 'clip.mp4' });
    expect(document.querySelector('video')?.getAttribute('src')).toBe('file://D:/v/clip.mp4');
    await userEvent.click(screen.getByRole('button', { name: t('ui.dialog.close') }));
    expect(onClose).toHaveBeenCalled();
  });
});

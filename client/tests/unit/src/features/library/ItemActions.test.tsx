import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { ItemActions } from '@/features/library/ItemActions';
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

beforeEach(() => api.post.mockResolvedValue({}));

describe('ItemActions (spec 020, D-4)', () => {
  it('«Mandar a…» abre la sección con la ruta; el Editor la agrega a una pista', async () => {
    wrap(<ItemActions item={libraryItem()} hasJob onDone={vi.fn()} />);

    await userEvent.click(screen.getByRole('button', { name: t('library.send.cleaner') }));
    expect(decodeURIComponent(window.location.hash)).toBe('#/cleaner?path=D:/out/narration/a/take.wav');
    await userEvent.click(screen.getByRole('button', { name: t('library.send.editor') }));
    expect(decodeURIComponent(window.location.hash)).toBe('#/editor?add=D:/out/narration/a/take.wav');
    expect(screen.getByRole('button', { name: t('library.send.normalize') })).toBeTruthy();
  });

  it('un video no ofrece Normalizar; un subtítulo no ofrece ninguna sección', () => {
    const { unmount } = wrap(<ItemActions item={libraryItem({ media_type: 'video' })} hasJob onDone={vi.fn()} />);
    expect(screen.queryByRole('button', { name: t('library.send.normalize') })).toBeNull();
    unmount();
    wrap(<ItemActions item={libraryItem({ media_type: 'subtitle' })} hasJob onDone={vi.fn()} />);
    expect(screen.queryByRole('button', { name: t('library.send.cleaner') })).toBeNull();
  });

  it('abre la carpeta, renombra y mueve', async () => {
    open.mockResolvedValueOnce('D:/destino').mockResolvedValueOnce(null);
    wrap(<ItemActions item={libraryItem()} hasJob onDone={vi.fn()} />);

    await userEvent.click(screen.getByRole('button', { name: t('media.action.folder') }));
    await userEvent.click(screen.getByRole('button', { name: t('library.rename') }));
    fireEvent.change(await screen.findByRole('textbox', { name: t('library.rename.name') }), { target: { value: 'final' } });
    await userEvent.click(screen.getAllByRole('button', { name: t('library.rename') }).at(-1) as HTMLElement);
    await userEvent.click(screen.getByRole('button', { name: t('library.move') }));
    await userEvent.click(screen.getByRole('button', { name: t('library.move') }));

    expect(openPath).toHaveBeenCalledWith('D:/out/narration/a');
    await waitFor(() => expect(api.post).toHaveBeenCalledWith('/library/1/rename', { name: 'final' }));
    await waitFor(() => expect(api.post).toHaveBeenCalledWith('/library/1/move', { folder: 'D:/destino' }));
    expect(api.post).toHaveBeenCalledTimes(2);
  });

  it('borrar con el archivo y el trabajo completo, o solo el registro con «no volver a agregar»', async () => {
    const onDone = vi.fn();
    const { unmount } = wrap(<ItemActions item={libraryItem()} hasJob onDone={onDone} />);
    await userEvent.click(screen.getByRole('button', { name: t('library.delete') }));
    await userEvent.click(await screen.findByRole('checkbox', { name: t('library.delete.files') }));
    await userEvent.click(await screen.findByRole('checkbox', { name: t('library.delete.whole_job') }));
    await userEvent.click(screen.getAllByRole('button', { name: t('library.delete') }).at(-1) as HTMLElement);
    await waitFor(() => expect(api.post).toHaveBeenCalledWith('/library/1/delete', { files: true, whole_job: true, ignore: false }));
    await waitFor(() => expect(onDone).toHaveBeenCalled());
    unmount();

    wrap(<ItemActions item={libraryItem({ origin: 'watched', job_id: null })} hasJob={false} onDone={vi.fn()} />);
    await userEvent.click(screen.getByRole('button', { name: t('library.delete') }));
    await userEvent.click(await screen.findByRole('checkbox', { name: t('library.delete.ignore') }));
    await userEvent.click(screen.getAllByRole('button', { name: t('library.delete') }).at(-1) as HTMLElement);
    await waitFor(() => expect(api.post).toHaveBeenLastCalledWith('/library/1/delete', { files: false, whole_job: false, ignore: true }));
  });

  it('un error del server al mover se avisa', async () => {
    api.post.mockRejectedValueOnce(new Error('Ya existe'));
    open.mockResolvedValueOnce('D:/destino');
    wrap(<ItemActions item={libraryItem()} hasJob onDone={vi.fn()} />);

    await userEvent.click(screen.getByRole('button', { name: t('library.move') }));

    await waitFor(() => expect(api.post).toHaveBeenCalledWith('/library/1/move', { folder: 'D:/destino' }));
  });
});

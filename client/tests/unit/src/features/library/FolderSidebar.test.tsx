import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { FolderSidebar } from '@/features/library/FolderSidebar';
import { t } from '@/shared/i18n/t';

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

beforeEach(() => {
  api.get.mockImplementation(async (path: string) =>
    path === '/library/folders' ? [{ id: 4, path: 'D:/videos', name: 'videos' }] : [{ id: 2, name: 'Curso', count: 3 }],
  );
  api.post.mockResolvedValue({});
  api.del.mockResolvedValue(null);
});

describe('FolderSidebar (spec 020, D-6)', () => {
  it('cambia de alcance entre Todo, Generado, una carpeta, un proyecto y Espacio', async () => {
    const onScope = vi.fn();
    wrap(<FolderSidebar scope={{ type: 'all' }} onScope={onScope} onAdded={vi.fn()} />);

    expect(screen.getByRole('button', { name: t('library.scope.all') }).getAttribute('aria-pressed')).toBe('true');
    await userEvent.click(screen.getByRole('button', { name: t('library.scope.generated') }));
    await userEvent.click(await screen.findByRole('button', { name: 'videos' }));
    await userEvent.click(await screen.findByRole('button', { name: t('library.projects.item', { name: 'Curso', count: 3 }) }));
    await userEvent.click(screen.getByRole('button', { name: t('library.scope.storage') }));

    expect(onScope.mock.calls.map(([scope]) => scope)).toEqual([
      { type: 'generated' },
      { type: 'folder', id: 4 },
      { type: 'project', id: 2 },
      { type: 'storage' },
    ]);
  });

  it('«Agregar carpeta…» vigila la elegida y escanea; la cruz deja de vigilarla', async () => {
    const onAdded = vi.fn();
    open.mockResolvedValueOnce('D:/nuevos').mockResolvedValueOnce(null);
    wrap(<FolderSidebar scope={{ type: 'all' }} onScope={vi.fn()} onAdded={onAdded} />);

    await userEvent.click(screen.getByRole('button', { name: t('library.folders.add') }));
    await waitFor(() => expect(api.post).toHaveBeenCalledWith('/library/folders', { path: 'D:/nuevos' }));
    await waitFor(() => expect(onAdded).toHaveBeenCalled());
    await userEvent.click(screen.getByRole('button', { name: t('library.folders.add') }));
    await userEvent.click(await screen.findByRole('button', { name: t('library.folders.remove', { name: 'videos' }) }));

    await waitFor(() => expect(api.del).toHaveBeenCalledWith('/library/folders/4'));
    expect(api.post).toHaveBeenCalledTimes(1);
  });

  it('«Nuevo proyecto» crea uno con el nombre escrito; un error se avisa', async () => {
    wrap(<FolderSidebar scope={{ type: 'all' }} onScope={vi.fn()} onAdded={vi.fn()} />);

    await userEvent.click(screen.getByRole('button', { name: t('library.projects.new') }));
    fireEvent.change(await screen.findByRole('textbox', { name: t('library.projects.name') }), { target: { value: 'Reels' } });
    await userEvent.click(screen.getByRole('button', { name: t('action.create') }));

    await waitFor(() => expect(api.post).toHaveBeenCalledWith('/projects', { name: 'Reels' }));
    api.post.mockRejectedValueOnce(new Error('no'));
    open.mockResolvedValueOnce('D:/mal');
    await userEvent.click(screen.getByRole('button', { name: t('library.folders.add') }));
    await waitFor(() => expect(api.post).toHaveBeenCalledWith('/library/folders', { path: 'D:/mal' }));
  });
});

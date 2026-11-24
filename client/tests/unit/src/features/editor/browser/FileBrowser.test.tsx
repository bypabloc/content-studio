import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { FileBrowser } from '@/features/editor/browser/FileBrowser';
import { t } from '@/shared/i18n/t';

const { api, dropState } = vi.hoisted(() => ({
  api: { get: vi.fn(), put: vi.fn(), queryUrl: vi.fn((path: string) => path) },
  dropState: { dragging: false, paths: ['D:\\Users\\Pablo\\Music\\grabacion.wav'] },
}));
vi.mock('@/shared/api/context', () => ({ useApi: () => api }));
vi.mock('@/features/editor/useNativeDrop', () => ({
  useNativeDrop: (onPaths: (paths: string[]) => void) => ({
    dragging: dropState.dragging,
    pick: async () => onPaths(dropState.paths),
  }),
}));

const ROOTS = [{ name: 'home', path: 'D:\\Users\\Pablo' }, { name: 'Music', path: 'D:\\Users\\Pablo\\Music' }];
const ENTRIES = [
  { name: 'Music', path: 'D:\\Users\\Pablo\\Music', kind: 'folder' },
  { name: 'voz.wav', path: 'D:\\Users\\Pablo\\voz.wav', kind: 'audio', size: 100, modified: 1 },
  { name: 'canción.mp3', path: 'D:\\Users\\Pablo\\canción.mp3', kind: 'audio', size: 200, modified: 2 },
  { name: 'video.mp4', path: 'D:\\Users\\Pablo\\video.mp4', kind: 'video', size: 300, modified: 3 },
  { name: 'portada.png', path: 'D:\\Users\\Pablo\\portada.png', kind: 'image', size: 400, modified: 4 },
];

beforeEach(() => {
  api.get.mockImplementation((url: string) => {
    if (url === '/fs/roots') return Promise.resolve({ roots: ROOTS });
    if (url === '/settings/editor.favorites') return Promise.resolve({ value: [] });
    if (url.startsWith('/fs/list?')) return Promise.resolve({ path: ROOTS[0].path, entries: ENTRIES });
    return Promise.reject(new Error('unknown endpoint'));
  });
  api.put.mockResolvedValue({});
  dropState.dragging = false;
  dropState.paths = ['D:\\Users\\Pablo\\Music\\grabacion.wav'];
  vi.spyOn(HTMLMediaElement.prototype, 'play').mockResolvedValue(undefined);
  vi.spyOn(HTMLMediaElement.prototype, 'pause').mockImplementation(() => undefined);
});

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
  vi.clearAllMocks();
});

describe('FileBrowser', () => {
  it('carga el árbol de carpetas y los archivos de medios', async () => {
    render(<FileBrowser onImport={vi.fn()} />);

    expect(await screen.findByRole('button', { name: 'voz.wav' })).toBeTruthy();
    expect(screen.getByRole('tree', { name: t('editor.browser.tree') })).toBeTruthy();
  });

  it('filtra por nombre y reproduce la vista previa al pasar por un audio', async () => {
    render(<FileBrowser onImport={vi.fn()} />);
    const file = await screen.findByRole('button', { name: 'voz.wav' });
    fireEvent.mouseEnter(file);

    expect(screen.queryByRole('button', { name: 'canción.mp3' })).toBeTruthy();
    fireEvent.change(screen.getByRole('searchbox', { name: t('editor.browser.search') }), { target: { value: 'voz' } });
    await waitFor(() => expect(screen.queryByRole('button', { name: 'canción.mp3' })).toBeNull());
    expect(api.queryUrl).toHaveBeenCalledWith('/fs/media', { path: 'D:\\Users\\Pablo\\voz.wav' });
  });

  it('importa las rutas seleccionadas con el diálogo nativo y guarda favoritas', async () => {
    const onImport = vi.fn();
    render(<FileBrowser onImport={onImport} />);
    fireEvent.click(await screen.findByRole('button', { name: t('action.import') }));

    expect(onImport).toHaveBeenCalledWith(['D:\\Users\\Pablo\\Music\\grabacion.wav']);
    fireEvent.click(screen.getByRole('button', { name: t('editor.browser.favorite', { name: 'home' }) }));
    await waitFor(() => expect(api.put).toHaveBeenCalledWith('/settings/editor.favorites', { value: [ROOTS[0].path] }));
  });

  it('mezcla favoritas guardadas, navega a ellas y marca el arrastre nativo', async () => {
    dropState.dragging = true;
    api.get.mockImplementation((url: string) => {
      if (url === '/fs/roots') return Promise.resolve({ roots: ROOTS });
      if (url === '/settings/editor.favorites') return Promise.resolve({ value: [ROOTS[0].path, 'D:\\Archive\\Audio'] });
      if (url.startsWith('/fs/list?')) return Promise.resolve({ path: ROOTS[0].path, entries: ENTRIES });
      return Promise.reject(new Error('unknown endpoint'));
    });
    render(<FileBrowser onImport={vi.fn()} />);

    const region = screen.getByRole('region', { name: t('editor.browser.label') });
    expect(region.className).toContain('border-primary');
    fireEvent.click(await screen.findByRole('treeitem', { name: 'Audio' }));
    await waitFor(() => expect(api.get.mock.calls.filter(([url]) => String(url).startsWith('/fs/list?')).length).toBeGreaterThan(1));
  });

  it('selecciona varios archivos, arrastra sus rutas y activa la vista previa por teclado', async () => {
    render(<FileBrowser onImport={vi.fn()} />);
    const voice = await screen.findByRole('button', { name: 'voz.wav' });
    const song = screen.getByRole('button', { name: 'canción.mp3' });
    fireEvent.click(voice);
    fireEvent.click(song, { ctrlKey: true });
    const dataTransfer = { setData: vi.fn() };
    fireEvent.dragStart(song, { dataTransfer });
    expect(dataTransfer.setData).toHaveBeenCalledWith(
      'application/x-content-studio-paths',
      JSON.stringify([`${ROOTS[0].path}\\voz.wav`, `${ROOTS[0].path}\\canción.mp3`]),
    );
    fireEvent.click(voice);
    const singleTransfer = { setData: vi.fn() };
    fireEvent.dragStart(song, { dataTransfer: singleTransfer });
    expect(singleTransfer.setData).toHaveBeenCalledWith('application/x-content-studio-paths', JSON.stringify([`${ROOTS[0].path}\\canción.mp3`]));
    fireEvent.keyDown(voice, { key: ' ' });
    fireEvent.keyDown(voice, { key: 'Enter' });
    await waitFor(() => expect(api.queryUrl).toHaveBeenCalledWith('/fs/media', { path: `${ROOTS[0].path}\\voz.wav` }));
    fireEvent.mouseLeave(voice);
  });

  it('restaura favoritas y muestra el error si falla el guardado', async () => {
    api.get.mockImplementation((url: string) => {
      if (url === '/fs/roots') return Promise.resolve({ roots: ROOTS });
      if (url === '/settings/editor.favorites') return Promise.resolve({ value: [ROOTS[0].path] });
      if (url.startsWith('/fs/list?')) return Promise.resolve({ path: ROOTS[0].path, entries: ENTRIES });
      return Promise.reject(new Error('unknown endpoint'));
    });
    api.put.mockRejectedValueOnce(new Error('save failed'));
    render(<FileBrowser onImport={vi.fn()} />);
    fireEvent.click(await screen.findByRole('button', { name: t('editor.browser.unfavorite', { name: 'home' }) }));

    expect(await screen.findByText(t('editor.browser.load_error'))).toBeTruthy();
    expect(screen.getByRole('button', { name: t('editor.browser.unfavorite', { name: 'home' }) })).toBeTruthy();
  });

  it('muestra un error si no puede cargar las raíces o la carpeta actual', async () => {
    api.get.mockRejectedValueOnce(new Error('roots unavailable'));
    render(<FileBrowser onImport={vi.fn()} />);
    expect(await screen.findByText(t('editor.browser.load_error'))).toBeTruthy();

    cleanup();
    api.get.mockImplementation((url: string) => {
      if (url === '/fs/roots') return Promise.resolve({ roots: ROOTS });
      if (url === '/settings/editor.favorites') return Promise.resolve({ value: [] });
      return Promise.reject(new Error('folder unavailable'));
    });
    render(<FileBrowser onImport={vi.fn()} />);
    expect(await screen.findByText(t('editor.browser.load_error'))).toBeTruthy();
  });

  it('navega por carpetas y filtra los tipos de medio sin ocultar carpetas', async () => {
    render(<FileBrowser onImport={vi.fn()} />);
    const fileList = screen.getByRole('list', { name: t('editor.browser.files') });
    await within(fileList).findByRole('button', { name: 'voz.wav' });
    fireEvent.click(within(fileList).getByRole('button', { name: 'Music' }));
    await waitFor(() => expect(api.get.mock.calls.filter(([url]) => String(url).startsWith('/fs/list?')).length).toBeGreaterThan(1));
    fireEvent.click(screen.getByRole('button', { name: t('editor.browser.up') }));
    await waitFor(() => expect(api.get.mock.calls.filter(([url]) => String(url).startsWith('/fs/list?')).length).toBeGreaterThan(2));
    const filter = screen.getByRole('combobox');
    await userEvent.click(filter);
    await userEvent.keyboard('{ArrowDown}{ArrowDown}{Enter}');

    expect(screen.getByRole('button', { name: 'Music' })).toBeTruthy();
    expect(screen.getByRole('button', { name: 'video.mp4' })).toBeTruthy();
    expect(screen.queryByRole('button', { name: 'voz.wav' })).toBeNull();
  });

  it('permite una sesión sin raíces y no solicita una carpeta vacía', async () => {
    api.get.mockImplementation((url: string) => {
      if (url === '/fs/roots') return Promise.resolve({ roots: [] });
      if (url === '/settings/editor.favorites') return Promise.resolve({ value: [] });
      return Promise.reject(new Error('unexpected endpoint'));
    });
    render(<FileBrowser onImport={vi.fn()} />);

    expect(await screen.findByText(t('editor.browser.empty'))).toBeTruthy();
    expect(api.get.mock.calls.some(([url]) => String(url).startsWith('/fs/list?'))).toBe(false);
    const favorite = screen.getAllByRole('button').find((button) => button.getAttribute('aria-label')?.includes('favoritas'));
    expect(favorite?.hasAttribute('disabled')).toBe(true);
  });

  it('muestra las rutas de navegación de un directorio POSIX', async () => {
    api.get.mockImplementation((url: string) => {
      if (url === '/fs/roots') return Promise.resolve({ roots: [{ name: 'pablo', path: '/home/pablo' }] });
      if (url === '/settings/editor.favorites') return Promise.resolve({ value: [] });
      if (url.startsWith('/fs/list?')) return Promise.resolve({ path: '/home/pablo', entries: [] });
      return Promise.reject(new Error('unknown endpoint'));
    });
    render(<FileBrowser onImport={vi.fn()} />);

    const breadcrumb = await screen.findByRole('navigation', { name: t('editor.browser.breadcrumb') });

    expect(within(breadcrumb).getByRole('button', { name: 'home' })).toBeTruthy();
    expect(within(breadcrumb).getByRole('button', { name: 'pablo' })).toBeTruthy();
  });
});

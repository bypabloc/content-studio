import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { EditorPage } from '@/features/editor/EditorPage';
import type { Doc } from '@/features/editor/model/types';
import { t } from '@/shared/i18n/t';

const { api, open } = vi.hoisted(() => ({ api: { get: vi.fn(), post: vi.fn(), put: vi.fn() }, open: vi.fn() }));
vi.mock('@/shared/api/context', () => ({ useApi: () => api }));
vi.mock('@tauri-apps/plugin-dialog', () => ({ open }));

const PATH = 'D:/out/editor/2026-11-22-demo/project.json';
const doc: Doc = {
  version: 1,
  name: 'demo',
  sample_rate: 48000,
  tracks: [{ id: 'voice', kind: 'audio', name: 'Voz', volume_db: 0, mute: false, solo: false, locked: false, height: 80 }],
  clips: [],
  markers: [],
};
const project = { path: PATH, hash: 'hash-1', doc, missing: [] };

beforeEach(() => {
  api.get.mockImplementation((url: string) =>
    url === '/editor/projects/recent' ? Promise.resolve({ paths: [] }) : Promise.resolve(project),
  );
  api.post.mockResolvedValue(project);
  api.put.mockResolvedValue({ hash: 'hash-2', missing: [] });
  open.mockResolvedValue(null);
});

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe('EditorPage', () => {
  it('crea un proyecto y conecta las operaciones con deshacer y rehacer', async () => {
    render(<EditorPage />);
    fireEvent.click(await screen.findByRole('button', { name: t('mix.create') }));

    expect(api.post).toHaveBeenCalledWith('/editor/projects', { name: t('editor.project.default_name') });
    expect(await screen.findByText('demo')).toBeTruthy();

    fireEvent.click(screen.getByRole('button', { name: t('editor.track.mute', { name: 'Voz' }) }));
    expect(screen.getByRole('button', { name: t('editor.track.mute', { name: 'Voz' }) }).getAttribute('aria-pressed')).toBe(
      'true',
    );
    fireEvent.click(screen.getByRole('button', { name: t('editor.history.undo') }));
    expect(screen.getByRole('button', { name: t('editor.track.mute', { name: 'Voz' }) }).getAttribute('aria-pressed')).toBe(
      'false',
    );
    fireEvent.click(screen.getByRole('button', { name: t('editor.history.redo') }));
    expect(screen.getByRole('button', { name: t('editor.track.mute', { name: 'Voz' }) }).getAttribute('aria-pressed')).toBe(
      'true',
    );
    const arm = screen.getByRole('button', { name: t('editor.track.arm', { name: 'Voz' }) });
    fireEvent.click(arm);
    expect(arm.getAttribute('aria-pressed')).toBe('true');
    fireEvent.click(arm);
    expect(arm.getAttribute('aria-pressed')).toBe('false');
  });

  it('abre un proyecto reciente y carga su hash para el siguiente guardado', async () => {
    api.get.mockImplementation((url: string) =>
      url === '/editor/projects/recent' ? Promise.resolve({ paths: [PATH] }) : Promise.resolve(project),
    );
    render(<EditorPage />);

    fireEvent.click(await screen.findByRole('button', { name: t('editor.project.open', { name: '2026-11-22-demo' }) }));

    expect(api.get).toHaveBeenLastCalledWith(`/editor/projects?path=${encodeURIComponent(PATH)}`);
    expect(await screen.findByRole('toolbar', { name: t('editor.transport.label') })).toBeTruthy();

    fireEvent.keyDown(screen.getByRole('group', { name: t('editor.timeline.label') }), { key: 'n' });
    expect(screen.getByRole('button', { name: t('editor.transport.magnet') }).getAttribute('aria-pressed')).toBe('false');

    const workspace = screen.getByRole('region', { name: t('editor.project.workspace', { name: 'demo' }) });
    fireEvent.keyDown(workspace, { key: 'Home' });
    fireEvent.keyDown(workspace, { key: 'r' });
    expect(await screen.findByText(t('editor.recorder.arm_track'))).toBeTruthy();
    expect(screen.getByRole('button', { name: t('voices.record.start') }).getAttribute('aria-pressed')).toBe('false');
    fireEvent.keyDown(workspace, { key: '+' });
    expect(screen.getByRole('group', { name: t('editor.timeline.ruler') }).getAttribute('style')).toContain('width: 1600px');
    fireEvent.keyDown(workspace, { key: '=' });
    expect(screen.getByRole('group', { name: t('editor.timeline.ruler') }).getAttribute('style')).toContain('width: 3200px');
    fireEvent.keyDown(workspace, { key: '-' });
    fireEvent.keyDown(workspace, { key: '_' });
    fireEvent.keyDown(workspace, { key: 'Spacebar' });
    fireEvent.keyDown(workspace, { key: 'x' });
    fireEvent.keyDown(workspace, { key: 'r', repeat: true });
    expect(screen.getByRole('button', { name: t('voices.record.start') }).getAttribute('aria-pressed')).toBe('false');

    fireEvent.keyDown(screen.getByRole('toolbar', { name: t('editor.transport.label') }), { key: 'n' });
    expect(screen.getByRole('button', { name: t('editor.transport.magnet') }).getAttribute('aria-pressed')).toBe('true');
  });

  it('abre un proyecto desde una carpeta elegida con el diálogo nativo', async () => {
    open.mockResolvedValue('D:\\Proyectos\\demo');
    render(<EditorPage />);
    fireEvent.click(await screen.findByRole('button', { name: t('editor.project.open_file') }));

    expect(open).toHaveBeenCalledWith({ directory: true, multiple: false });
    await waitFor(() => expect(api.get).toHaveBeenCalledWith(
      `/editor/projects?path=${encodeURIComponent('D:\\Proyectos\\demo\\project.json')}`,
    ));
    expect(await screen.findByRole('toolbar', { name: t('editor.transport.label') })).toBeTruthy();
  });

  it('crea un proyecto y arma su primera pista al grabar desde Inicio', async () => {
    render(<EditorPage />);
    fireEvent.click(await screen.findByRole('button', { name: t('voices.record.start') }));

    expect(api.post).toHaveBeenCalledWith('/editor/projects', { name: t('editor.project.default_name') });
    const arm = await screen.findByRole('button', { name: t('editor.track.arm', { name: 'Voz' }) });
    expect(arm.getAttribute('aria-pressed')).toBe('true');
  });

  it('muestra el estado de carga y el estado vacío de proyectos recientes', async () => {
    render(<EditorPage />);

    expect(screen.getByText(t('editor.project.loading'))).toBeTruthy();
    expect(await screen.findByText(t('editor.project.empty'))).toBeTruthy();
  });

  it('muestra un error localizado si no puede cargar los proyectos recientes', async () => {
    api.get.mockRejectedValueOnce(new Error('offline'));
    render(<EditorPage />);

    expect(await screen.findByText(t('editor.project.load_error'))).toBeTruthy();
    expect(screen.getByText(t('editor.project.empty'))).toBeTruthy();
  });

  it('muestra un error localizado si falla la apertura o creación', async () => {
    api.get.mockImplementation((url: string) =>
      url === '/editor/projects/recent' ? Promise.resolve({ paths: [PATH] }) : Promise.reject(new Error('offline')),
    );
    render(<EditorPage />);
    fireEvent.click(await screen.findByRole('button', { name: t('editor.project.open', { name: '2026-11-22-demo' }) }));
    expect(await screen.findByText(t('editor.project.load_error'))).toBeTruthy();

    cleanup();
    api.get.mockResolvedValue({ paths: [] });
    api.post.mockRejectedValueOnce(new Error('offline'));
    render(<EditorPage />);
    fireEvent.click(await screen.findByRole('button', { name: t('mix.create') }));
    expect(await screen.findByText(t('editor.project.load_error'))).toBeTruthy();
  });

  it('usa la ruta completa cuando una entrada reciente no tiene carpeta contenedora', async () => {
    api.get.mockImplementation((url: string) =>
      url === '/editor/projects/recent' ? Promise.resolve({ paths: ['project.json'] }) : Promise.resolve(project),
    );
    render(<EditorPage />);
    fireEvent.click(await screen.findByRole('button', { name: t('editor.project.open', { name: 'project.json' }) }));
    expect(await screen.findByRole('toolbar', { name: t('editor.transport.label') })).toBeTruthy();
  });

  it('ignora la cancelación del diálogo y abre una carpeta POSIX', async () => {
    render(<EditorPage />);
    fireEvent.click(await screen.findByRole('button', { name: t('editor.project.open_file') }));
    await waitFor(() => expect(open).toHaveBeenCalledWith({ directory: true, multiple: false }));
    expect(api.get).toHaveBeenCalledTimes(1);

    cleanup();
    open.mockResolvedValueOnce('/home/pablo/editor/');
    api.get.mockImplementation((url: string) =>
      url === '/editor/projects/recent' ? Promise.resolve({ paths: [] }) : Promise.resolve(project),
    );
    render(<EditorPage />);
    fireEvent.click(await screen.findByRole('button', { name: t('editor.project.open_file') }));
    await waitFor(() => expect(api.get).toHaveBeenCalledWith(
      `/editor/projects?path=${encodeURIComponent('/home/pablo/editor/project.json')}`,
    ));
  });

  it('muestra un error si el diálogo nativo no puede abrirse', async () => {
    open.mockRejectedValueOnce('dialog unavailable');
    render(<EditorPage />);
    fireEvent.click(await screen.findByRole('button', { name: t('editor.project.open_file') }));

    expect(await screen.findByText(t('editor.project.load_error'))).toBeTruthy();
  });
});

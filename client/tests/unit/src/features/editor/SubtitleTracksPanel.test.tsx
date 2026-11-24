import { act, cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { SubtitleTracksPanel } from '@/features/editor/SubtitleTracksPanel';
import type { Doc } from '@/features/editor/model/types';
import { t } from '@/shared/i18n/t';

const mocks = vi.hoisted(() => ({ api: { get: vi.fn(), post: vi.fn() } }));
vi.mock('@/shared/api/context', () => ({ useApi: () => mocks.api }));

const doc: Doc = {
  version: 3,
  name: 'Prueba',
  sample_rate: 48000,
  canvas: { width: 320, height: 180, fps: 30, background: '#000000' },
  tracks: [],
  clips: [],
  markers: [],
  transitions: [],
};
const audioDoc: Doc = {
  ...doc,
  clips: [{ id: 'audio', track: 'audio', src: 'voz.wav', src_in: 0, src_out: 1, start: 0, fade_in: 0, fade_out: 0, gain_db: 0 }],
};

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe('SubtitleTracksPanel', () => {
  it('agrega un proyecto existente como una pista del editor', async () => {
    mocks.api.get.mockResolvedValue([{ id: 4, name: 'Proyecto de subtítulos' }]);
    const onAdd = vi.fn();
    render(<SubtitleTracksPanel doc={doc} path="project.json" onAdd={onAdd} />);
    const picker = await screen.findByRole('combobox', { name: t('editor.subtitles.project') });
    await userEvent.click(picker);
    await userEvent.click(await screen.findByRole('option', { name: 'Proyecto de subtítulos' }));
    await userEvent.click(screen.getByRole('button', { name: t('editor.subtitles.add') }));

    expect(onAdd).toHaveBeenCalledWith(expect.objectContaining({
      kind: 'subtitles',
      name: 'Proyecto de subtítulos',
      subtitles_project: '4',
    }));
    expect((screen.getByRole('button', { name: t('editor.subtitles.transcribe') }) as HTMLButtonElement).disabled).toBe(true);
  });

  it('renderiza la mezcla, encola transcribe y crea la pista con el proyecto resultante', async () => {
    mocks.api.get.mockImplementation((url: string) => {
      if (url === '/subtitles') return Promise.resolve([]);
      if (url === '/jobs/10') return Promise.resolve({ id: 10, status: 'done', progress: 1, result: { output: 'mix.wav' } });
      if (url === '/jobs/11') return Promise.resolve({ id: 11, status: 'done', progress: 1, result: null });
      return Promise.reject(new Error(url));
    });
    mocks.api.post.mockImplementation((url: string, body: { kind?: string }) => {
      if (url === '/jobs' && body.kind === 'editor.render') return Promise.resolve({ id: 10, status: 'queued', progress: 0 });
      if (url === '/jobs' && body.kind === 'transcribe') return Promise.resolve({ id: 11, status: 'queued', progress: 0 });
      if (url === '/subtitles/from-transcript') return Promise.resolve({ id: 7, name: 'mix' });
      return Promise.reject(new Error(url));
    });
    const onAdd = vi.fn();
    render(<SubtitleTracksPanel doc={audioDoc} path="project.json" onAdd={onAdd} />);

    await userEvent.click(await screen.findByRole('button', { name: t('editor.subtitles.transcribe') }));

    await waitFor(() => expect(onAdd).toHaveBeenCalledWith(expect.objectContaining({ subtitles_project: '7' })));
    expect(mocks.api.post).toHaveBeenNthCalledWith(1, '/jobs', expect.objectContaining({
      kind: 'editor.render',
      params: expect.objectContaining({ doc: 'project.json', format: 'wav' }),
    }));
    expect(mocks.api.post).toHaveBeenNthCalledWith(2, '/jobs', expect.objectContaining({
      kind: 'transcribe',
      params: expect.objectContaining({ input: 'mix.wav', model: 'large-v3-turbo' }),
    }));
    expect(mocks.api.post).toHaveBeenNthCalledWith(3, '/subtitles/from-transcript', { job_id: 11 });
  });

  it.each(['error', 'cancelled'] as const)('muestra el error si la mezcla termina en %s', async (status) => {
    mocks.api.get.mockImplementation((url: string) => {
      if (url === '/subtitles') return Promise.resolve([]);
      if (url === '/jobs/10') return Promise.resolve({ id: 10, status, progress: 0, result: null });
      return Promise.reject(new Error(url));
    });
    mocks.api.post.mockResolvedValue({ id: 10, status: 'queued', progress: 0 });
    render(<SubtitleTracksPanel doc={audioDoc} path="project.json" onAdd={vi.fn()} />);

    await userEvent.click(await screen.findByRole('button', { name: t('editor.subtitles.transcribe') }));

    expect(await screen.findByText(t('editor.subtitles.error'))).toBeTruthy();
  });

  it('muestra el error si el render no devuelve una mezcla', async () => {
    mocks.api.get.mockImplementation((url: string) => {
      if (url === '/subtitles') return Promise.resolve([]);
      if (url === '/jobs/10') return Promise.resolve({ id: 10, status: 'done', progress: 1, result: null });
      return Promise.reject(new Error(url));
    });
    mocks.api.post.mockResolvedValue({ id: 10, status: 'queued', progress: 0 });
    render(<SubtitleTracksPanel doc={audioDoc} path="project.json" onAdd={vi.fn()} />);

    await userEvent.click(await screen.findByRole('button', { name: t('editor.subtitles.transcribe') }));

    expect(await screen.findByText(t('editor.subtitles.error'))).toBeTruthy();
  });

  it('indica que está trabajando mientras espera el trabajo de mezcla', async () => {
    mocks.api.get.mockImplementation((url: string) => {
      if (url === '/subtitles') return Promise.resolve([]);
      return new Promise(() => undefined);
    });
    mocks.api.post.mockResolvedValue({ id: 10, status: 'queued', progress: 0 });
    render(<SubtitleTracksPanel doc={audioDoc} path="project.json" onAdd={vi.fn()} />);

    fireEvent.click(await screen.findByRole('button', { name: t('editor.subtitles.transcribe') }));

    expect(await screen.findByRole('button', { name: t('editor.subtitles.working') })).toBeTruthy();
  });

  it('ignora la lista de proyectos que llega después de desmontar el panel', async () => {
    let resolveProjects!: (projects: never[]) => void;
    mocks.api.get.mockReturnValue(new Promise((resolve) => { resolveProjects = resolve; }));
    const { unmount } = render(<SubtitleTracksPanel doc={doc} path="project.json" onAdd={vi.fn()} />);

    unmount();
    await act(async () => resolveProjects([]));
  });

  it('muestra el error si no puede cargar los proyectos', async () => {
    mocks.api.get.mockRejectedValue(new Error('offline'));
    render(<SubtitleTracksPanel doc={doc} path="project.json" onAdd={vi.fn()} />);

    expect(await screen.findByText(t('editor.subtitles.error'))).toBeTruthy();
  });
});

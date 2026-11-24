import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { act, cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { SubtitlesEditor } from '@/features/subtitles/SubtitlesEditor';
import { BUILTIN_PRESETS } from '@/features/subtitles/presets';
import { toast } from '@/shared/components/molecules/UIToast';
import { t } from '@/shared/i18n/t';

const { api } = vi.hoisted(() => ({
  api: { get: vi.fn(), put: vi.fn(), post: vi.fn(), del: vi.fn(), fileUrl: (path: string) => `file://${path}` },
}));
vi.mock('@/shared/api/context', () => ({ useApi: () => api }));
// JASSUB se prueba aparte (SubtitlesPreview): aquí el editor solo recibe el ASS.
vi.mock('@/features/subtitles/SubtitlesPreview', () => ({ SubtitlesPreview: () => null }));
vi.mock('@/shared/components/molecules/UIToast', () => ({ toast: { error: vi.fn() } }));

const word = (start: number, end: number, text: string) => ({ start, end, text, keyword: null });
const doc = {
  version: 1,
  source: { path: 'charla.mp4', kind: 'file' },
  language: 'es',
  style: {},
  tracks: {},
  cues: [
    { id: 1, start: 0, end: 2, text: 'hola a todos', words: [word(0, 0.5, 'hola'), word(0.5, 1, 'a'), word(1, 2, 'todos')] },
    { id: 2, start: 2.5, end: 4, text: 'buenas tardes', words: [word(2.5, 3, 'buenas'), word(3, 4, 'tardes')] },
  ],
};

function renderEditor() {
  return render(
    <QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>
      <SubtitlesEditor projectId={7} />
    </QueryClientProvider>,
  );
}

describe('SubtitlesEditor', () => {
  beforeEach(() => {
    api.get.mockImplementation(async (path: string) => (path === '/subtitles/7' ? structuredClone(doc) : { key: 'x', value: undefined }));
    api.put.mockImplementation(async (_path: string, body: unknown) => body);
  });
  afterEach(() => {
    cleanup();
    vi.useRealTimers();
    vi.clearAllMocks();
  });

  it('saves the edited document once, one second after the last change', async () => {
    renderEditor();
    const field = await screen.findByDisplayValue('hola a todos');
    vi.useFakeTimers();
    fireEvent.change(field, { target: { value: 'hola a amigos' } });

    expect(api.put).not.toHaveBeenCalled();
    await act(async () => vi.advanceTimersByTimeAsync(999));
    expect(api.put).not.toHaveBeenCalled();
    await act(async () => vi.advanceTimersByTimeAsync(1));
    expect(api.put).toHaveBeenCalledTimes(1);

    expect(api.put.mock.calls[0][0]).toBe('/subtitles/7');
    expect(api.put.mock.calls[0][1].cues[0].text).toBe('hola a amigos');
  });

  it('merges the current cue with the next one with the M shortcut', async () => {
    renderEditor();
    await screen.findByDisplayValue('hola a todos');

    fireEvent.keyDown(window, { key: 'm' });
    await waitFor(() => expect(api.put).toHaveBeenCalled(), { timeout: 3000 });

    expect(api.put.mock.calls.at(-1)?.[1].cues).toHaveLength(1);
  });

  it('moves the focus with the arrows, so S splits the cue that is focused', async () => {
    renderEditor();
    await screen.findByDisplayValue('hola a todos');

    fireEvent.keyDown(window, { key: 'ArrowRight' });
    fireEvent.keyDown(window, { key: 's' });

    await waitFor(() => expect(api.put).toHaveBeenCalled(), { timeout: 3000 });
    expect(api.put.mock.calls.at(-1)?.[1].cues).toHaveLength(3);
  });

  it('saves the draft before it enqueues the burn and translate jobs', async () => {
    renderEditor();
    fireEvent.change(await screen.findByDisplayValue('hola a todos'), { target: { value: 'hola a amigos' } });

    fireEvent.click(screen.getByRole('button', { name: t('subtitles.editor.burn') }));
    await waitFor(() =>
      expect(api.post).toHaveBeenCalledWith('/jobs', { kind: 'subtitles.burn', params: { project_id: 7 } }),
    );
    expect(api.put.mock.calls[0][1].cues[0].text).toBe('hola a amigos');

    fireEvent.click(screen.getByRole('button', { name: t('subtitles.editor.translate') }));
    await waitFor(() =>
      expect(api.post).toHaveBeenCalledWith('/jobs', { kind: 'subtitles.translate', params: { project_id: 7 } }),
    );
  });

  it('keeps a style change from the panel in the saved document', async () => {
    renderEditor();
    await screen.findByDisplayValue('hola a todos');

    fireEvent.click(screen.getByRole('switch', { name: t('subtitles.style.uppercase') }));

    await waitFor(() => expect(api.put).toHaveBeenCalled(), { timeout: 3000 });
    expect(api.put.mock.calls.at(-1)?.[1].style.uppercase).toBe(true);
  });

  it('does not run the shortcuts while a text field has the focus', async () => {
    renderEditor();
    const field = await screen.findByDisplayValue('hola a todos');

    fireEvent.keyDown(field, { key: 'm' });

    expect(field).toHaveProperty('value', 'hola a todos');
  });

  it('moves the focus back with the left arrow', async () => {
    renderEditor();
    await screen.findByDisplayValue('hola a todos');

    fireEvent.keyDown(window, { key: 'ArrowRight' });
    fireEvent.keyDown(window, { key: 'ArrowLeft' });
    fireEvent.keyDown(window, { key: 's' });

    await waitFor(() => expect(api.put).toHaveBeenCalled(), { timeout: 3000 });
    expect(api.put.mock.calls.at(-1)?.[1].cues).toHaveLength(3);
  });

  it('enqueues the burn job without saving when nothing changed', async () => {
    renderEditor();
    await screen.findByDisplayValue('hola a todos');

    fireEvent.click(screen.getByRole('button', { name: t('subtitles.editor.burn') }));

    await waitFor(() =>
      expect(api.post).toHaveBeenCalledWith('/jobs', { kind: 'subtitles.burn', params: { project_id: 7 } }),
    );
    expect(api.put).not.toHaveBeenCalled();
  });

  it('shows the style saved in the document in the panel', async () => {
    api.get.mockImplementation(async (path: string) =>
      path === '/subtitles/7' ? { ...structuredClone(doc), style: { ...BUILTIN_PRESETS.reels } } : { key: 'x', value: undefined },
    );
    renderEditor();

    const uppercase = await screen.findByRole('switch', { name: t('subtitles.style.uppercase') });
    expect(uppercase.getAttribute('aria-checked')).toBe('true');
  });

  it('exporta en el formato elegido y muestra la ruta del archivo', async () => {
    api.post.mockResolvedValue({ path: 'C:/out/subtitles/7-charla.ass' });
    renderEditor();
    await screen.findByDisplayValue('hola a todos');

    fireEvent.click(screen.getByRole('button', { name: t('subtitles.export.ass') }));

    await waitFor(() => expect(api.post).toHaveBeenCalledWith('/subtitles/7/export', { format: 'ass' }));
    expect(await screen.findByText(t('subtitles.export.done', { path: 'C:/out/subtitles/7-charla.ass' }))).toBeTruthy();
  });

  it('un error al exportar avisa con el texto que devuelve el server', async () => {
    api.post.mockRejectedValueOnce(new Error('El formato no existe'));
    renderEditor();
    await screen.findByDisplayValue('hola a todos');

    fireEvent.click(screen.getByRole('button', { name: t('subtitles.export.srt') }));

    await waitFor(() => expect(toast.error).toHaveBeenCalledWith('El formato no existe'));
  });

  it('un error al quemar avisa con el texto del server y no deja el editor roto', async () => {
    api.post.mockRejectedValueOnce(new Error('Este ffmpeg no trae libass'));
    renderEditor();
    await screen.findByDisplayValue('hola a todos');

    fireEvent.click(screen.getByRole('button', { name: t('subtitles.editor.burn') }));

    await waitFor(() => expect(toast.error).toHaveBeenCalledWith('Este ffmpeg no trae libass'));
    expect(screen.getByDisplayValue('hola a todos')).toBeTruthy();
  });
});

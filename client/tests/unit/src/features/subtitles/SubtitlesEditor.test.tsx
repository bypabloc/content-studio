import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { act, cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
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
    api.post.mockResolvedValue({ id: 42 });
  });
  afterEach(() => {
    cleanup();
    vi.useRealTimers();
    vi.clearAllMocks();
    window.location.hash = '';
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

  it('opens a burned video in the Editor after the burn job completes', async () => {
    api.post.mockResolvedValue({ id: 42 });
    api.get.mockImplementation(async (path: string) => {
      if (path === '/subtitles/7') return structuredClone(doc);
      if (path === '/jobs/42') return { id: 42, status: 'done', output_dir: 'out/subtitles/7' };
      if (path.startsWith('/fs/list?')) return { entries: [{ kind: 'video', path: 'out/subtitles/7/burned.mp4' }] };
      return { key: 'x', value: undefined };
    });
    renderEditor();

    fireEvent.click(await screen.findByRole('button', { name: t('subtitles.editor.burn') }));
    fireEvent.click(await screen.findByRole('button', { name: t('action.open_editor') }));

    await waitFor(() => {
      const query = new URLSearchParams(window.location.hash.split('?')[1]);
      expect(query.getAll('add')).toEqual(['out/subtitles/7/burned.mp4']);
    });
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

  it('exporta la pista traducida que se elige en el selector de pistas', async () => {
    api.get.mockImplementation(async (path: string) =>
      path === '/subtitles/7'
        ? { ...structuredClone(doc), tracks: { pt: [{ id: 1, start: 0, end: 2, text: 'olá a todos' }] } }
        : { key: 'x', value: undefined },
    );
    api.post.mockResolvedValue({ path: 'C:/out/subtitles/7-charla.pt.srt' });
    renderEditor();
    await screen.findByDisplayValue('hola a todos');

    await userEvent.click(screen.getByRole('combobox', { name: t('subtitles.editor.track') }));
    await userEvent.click(await screen.findByRole('option', { name: 'PT' }));
    fireEvent.click(screen.getByRole('button', { name: t('subtitles.export.srt') }));

    await waitFor(() =>
      expect(api.post).toHaveBeenCalledWith('/subtitles/7/export', { format: 'srt', language: 'pt' }),
    );
  });

  it('sin pistas traducidas no muestra el selector de pistas', async () => {
    renderEditor();
    await screen.findByDisplayValue('hola a todos');

    expect(screen.queryByRole('combobox', { name: t('subtitles.editor.track') })).toBeNull();
  });


const speakerDoc = {
  ...doc,
  speakers: { SPEAKER_00: { name: 'Ana', color: '#2563eb' }, SPEAKER_01: { name: 'Luis', color: '#dc2626' } },
  cues: [
    { ...doc.cues[0], speaker: 'SPEAKER_00' },
    { ...doc.cues[1], speaker: 'SPEAKER_01' },
  ],
};

describe('SubtitlesEditor with speakers', () => {
  it('shows the speaker legend and exports the names when asked', async () => {
    api.get.mockImplementation(async (path: string) => (path === '/subtitles/7' ? structuredClone(speakerDoc) : { key: 'x', value: undefined }));
    renderEditor();

    expect(await screen.findByRole('list', { name: t('speakers.legend.title') })).toBeTruthy();
    await userEvent.click(screen.getByRole('checkbox', { name: t('subtitles.export.speaker_labels') }));
    await userEvent.click(screen.getByRole('button', { name: t('subtitles.export.srt') }));

    await waitFor(() => expect(api.post).toHaveBeenCalledWith('/subtitles/7/export', { format: 'srt', speaker_labels: true }));
  });
});

  it('guarda el borrador antes de exportar, para que el archivo lleve el cambio recién hecho', async () => {
    api.get.mockImplementation(async (path: string) => (path === '/subtitles/7' ? structuredClone(speakerDoc) : { key: 'x', value: undefined }));
    renderEditor();

    const name = await screen.findByLabelText(t('speakers.legend.rename', { name: 'Ana' }));
    fireEvent.change(name, { target: { value: 'Ana M.' } });
    fireEvent.keyDown(name, { key: 'Enter' });
    fireEvent.click(screen.getByRole('button', { name: t('subtitles.export.srt') }));

    await waitFor(() => expect(api.post).toHaveBeenCalledWith('/subtitles/7/export', { format: 'srt' }));
    const saved = api.put.mock.calls.find((call) => call[0] === '/subtitles/7');
    expect(saved?.[1]).toMatchObject({ speakers: { SPEAKER_00: { name: 'Ana M.' } } });
    expect(api.put.mock.invocationCallOrder[0]).toBeLessThan(api.post.mock.invocationCallOrder[0]);
  });

});

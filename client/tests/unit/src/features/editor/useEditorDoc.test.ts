import { act, cleanup, renderHook } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { useEditorDoc } from '@/features/editor/useEditorDoc';
import type { AudioTrack, Doc } from '@/features/editor/model/types';

const { api } = vi.hoisted(() => ({ api: { put: vi.fn() } }));
vi.mock('@/shared/api/context', () => ({ useApi: () => api }));

const PATH = 'D:/projects/demo/project.json';

function document(): Doc {
  return {
    version: 2,
    name: 'demo',
    sample_rate: 48000,
    canvas: { width: 1920, height: 1080, fps: 30, background: '#000000' },
    tracks: [{ id: 't1', kind: 'audio', name: 'Voz', volume_db: 0, mute: false, solo: false, locked: false, height: 80 }],
    clips: [],
    markers: [],
    transitions: [],
  };
}

function renderDocument(doc = document()) {
  return renderHook(() => useEditorDoc({ path: PATH, doc, hash: 'hash-1' }));
}

function audioTrack(doc: Doc): AudioTrack {
  const track = doc.tracks[0];
  if (track?.kind !== 'audio') throw new Error('expected_audio_track');
  return track;
}

beforeEach(() => {
  vi.useFakeTimers();
  api.put.mockResolvedValue({ hash: 'hash-2', missing: [] });
});

afterEach(() => {
  cleanup();
  vi.useRealTimers();
  vi.clearAllMocks();
});

describe('useEditorDoc (spec 017, AC-6)', () => {
  it('aplica operaciones y deshace y rehace el cambio', () => {
    const { result } = renderDocument();

    act(() => {
      result.current.undo();
      result.current.redo();
    });
    expect(audioTrack(result.current.doc).mute).toBe(false);

    act(() => result.current.applyOp({ type: 'setTrack', id: 't1', changes: { mute: true } }));
    expect(audioTrack(result.current.doc).mute).toBe(true);
    expect(result.current.canUndo).toBe(true);

    act(() => result.current.undo());
    expect(audioTrack(result.current.doc).mute).toBe(false);

    act(() => result.current.redo());
    expect(audioTrack(result.current.doc).mute).toBe(true);
  });

  it('guarda después de 1 s con el hash actual en If-Match', async () => {
    const { result } = renderDocument();
    act(() => result.current.applyOp({ type: 'setTrack', id: 't1', changes: { mute: true } }));

    await act(async () => vi.advanceTimersByTimeAsync(999));
    expect(api.put).not.toHaveBeenCalled();

    await act(async () => vi.advanceTimersByTimeAsync(1));
    expect(api.put).toHaveBeenCalledWith(
      `/editor/projects?path=${encodeURIComponent(PATH)}`,
      expect.objectContaining({ tracks: [expect.objectContaining({ mute: true })] }),
      { 'If-Match': 'hash-1' },
    );
    expect(result.current.hash).toBe('hash-2');
    expect(result.current.saveState).toBe('saved');
  });

  it('reinicia el debounce y guarda solo el documento más reciente', async () => {
    const { result } = renderDocument();
    act(() => result.current.applyOp({ type: 'setTrack', id: 't1', changes: { mute: true } }));
    await act(async () => vi.advanceTimersByTimeAsync(500));
    act(() => result.current.applyOp({ type: 'setTrack', id: 't1', changes: { solo: true } }));

    await act(async () => vi.advanceTimersByTimeAsync(999));
    expect(api.put).not.toHaveBeenCalled();
    await act(async () => vi.advanceTimersByTimeAsync(1));

    expect(api.put).toHaveBeenCalledTimes(1);
    expect(api.put.mock.calls[0][1].tracks[0]).toMatchObject({ mute: true, solo: true });
  });

  it('conserva los cambios y expone el error si falla el guardado', async () => {
    api.put.mockRejectedValueOnce(new Error('project_changed'));
    const { result } = renderDocument();
    act(() => result.current.applyOp({ type: 'setTrack', id: 't1', changes: { mute: true } }));

    await act(async () => vi.advanceTimersByTimeAsync(1000));

    expect(audioTrack(result.current.doc).mute).toBe(true);
    expect(result.current.saveState).toBe('error');
    expect(result.current.saveError).toBe('project_changed');
  });

  it('agrupa el preview como un paso y lo puede cancelar antes de confirmar', () => {
    const { result } = renderDocument();
    const preview = document();
    audioTrack(preview).solo = true;

    act(() => result.current.previewDoc(preview));
    expect(audioTrack(result.current.doc).solo).toBe(true);
    expect(result.current.saveState).toBe('saved');
    act(() => result.current.commitPreview());
    expect(result.current.canUndo).toBe(true);
    expect(result.current.saveState).toBe('dirty');

    act(() => result.current.undo());
    expect(audioTrack(result.current.doc).solo).toBe(false);
    act(() => result.current.redo());
    expect(audioTrack(result.current.doc).solo).toBe(true);

    const nextPreview = document();
    audioTrack(nextPreview).mute = true;
    act(() => result.current.previewDoc(nextPreview));
    act(() => result.current.cancelPreview());
    expect(audioTrack(result.current.doc).solo).toBe(true);
    expect(audioTrack(result.current.doc).mute).toBe(false);
    act(() => result.current.cancelPreview());
    act(() => result.current.commitPreview());
  });

  it('reintenta guardar cambios nuevos si el guardado anterior falla mientras estaba en curso', async () => {
    let rejectFirst!: (reason?: unknown) => void;
    api.put.mockImplementationOnce(
      () => new Promise((_, reject: (reason?: unknown) => void) => { rejectFirst = reject; }),
    );
    const { result } = renderDocument();
    act(() => result.current.applyOp({ type: 'setTrack', id: 't1', changes: { mute: true } }));
    await act(async () => vi.advanceTimersByTimeAsync(1000));
    expect(api.put).toHaveBeenCalledTimes(1);

    act(() => result.current.applyOp({ type: 'setTrack', id: 't1', changes: { solo: true } }));
    await act(async () => vi.advanceTimersByTimeAsync(1000));
    await act(async () => {
      rejectFirst(new Error('project_changed'));
      await Promise.resolve();
    });
    expect(result.current.saveState).toBe('error');

    await act(async () => vi.advanceTimersByTimeAsync(1000));
    expect(api.put).toHaveBeenCalledTimes(2);
    expect(api.put.mock.calls[1][1].tracks[0]).toMatchObject({ mute: true, solo: true });
    expect(result.current.saveState).toBe('saved');
  });

  it('convierte a texto un error de guardado que no es Error', async () => {
    api.put.mockRejectedValueOnce('offline');
    const { result } = renderDocument();
    act(() => result.current.applyOp({ type: 'setTrack', id: 't1', changes: { mute: true } }));

    await act(async () => vi.advanceTimersByTimeAsync(1000));

    expect(result.current.saveState).toBe('error');
    expect(result.current.saveError).toBe('offline');
  });

  it('cancela un guardado pendiente al desmontar', async () => {
    const { result, unmount } = renderDocument();
    act(() => result.current.applyOp({ type: 'setTrack', id: 't1', changes: { mute: true } }));

    unmount();
    await act(async () => vi.advanceTimersByTimeAsync(1000));

    expect(api.put).not.toHaveBeenCalled();
  });
});

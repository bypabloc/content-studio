import { cleanup, renderHook, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { useEditorMediaImport } from '@/features/editor/useEditorMediaImport';
import type { Doc, Op } from '@/features/editor/model/types';

const { api } = vi.hoisted(() => ({ api: { get: vi.fn() } }));
vi.mock('@/shared/api/context', () => ({ useApi: () => api }));

const base = {
  tracks: [] as Doc['tracks'],
  trackCount: 0,
  applyOp: vi.fn<(op: Op) => void>(),
  position: 2,
};

beforeEach(() => {
  api.get.mockResolvedValue({ duration: 3, kind: 'audio', has_audio: true });
});

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe('useEditorMediaImport', () => {
  it('imports requested paths at the playhead once and acknowledges completion', async () => {
    const onAddHandled = vi.fn();
    const options = { ...base, pendingAdd: ['D:/media/voice.wav'], onAddHandled };
    const { result, rerender } = renderHook(() => useEditorMediaImport(options));

    await waitFor(() => expect(onAddHandled).toHaveBeenCalledTimes(1));
    expect(api.get).toHaveBeenCalledWith('/fs/info?path=D%3A%2Fmedia%2Fvoice.wav');
    expect(base.applyOp).toHaveBeenCalledWith(
      expect.objectContaining({ type: 'addClip', clip: expect.objectContaining({ src: 'D:/media/voice.wav', start: 2 }) }),
    );

    rerender();
    expect(api.get).toHaveBeenCalledTimes(1);
    expect(result.current.importError).toBe(false);
  });

  it('does not import an empty request and accepts paths added later', async () => {
    const onAddHandled = vi.fn();
    const { rerender } = renderHook(
      ({ pendingAdd }: { pendingAdd: string[] }) => useEditorMediaImport({ ...base, pendingAdd, onAddHandled }),
      { initialProps: { pendingAdd: [] as string[] } },
    );

    expect(api.get).not.toHaveBeenCalled();
    rerender({ pendingAdd: ['D:/media/voice.wav'] });
    await waitFor(() => expect(onAddHandled).toHaveBeenCalledTimes(1));
    expect(api.get).toHaveBeenCalledTimes(1);
  });

  it('reports invalid media and still acknowledges the request', async () => {
    api.get.mockResolvedValue({ duration: 0, kind: 'audio', has_audio: true });
    const onAddHandled = vi.fn();
    const { result } = renderHook(() =>
      useEditorMediaImport({ ...base, pendingAdd: ['D:/media/invalid.wav'], onAddHandled }),
    );

    await waitFor(() => expect(result.current.importError).toBe(true));
    expect(onAddHandled).toHaveBeenCalledTimes(1);
    expect(base.applyOp).not.toHaveBeenCalled();
  });
});

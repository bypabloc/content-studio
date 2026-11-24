import { act, renderHook } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { useTrackRecorder } from '@/features/editor/useTrackRecorder';

const { api, recorder } = vi.hoisted(() => ({
  api: { upload: vi.fn() },
  recorder: {
    recording: false,
    sampleRate: 48000,
    levels: { peak: -60, rms: -60 },
    latencyMs: 27,
    start: vi.fn(),
    stop: vi.fn(),
  },
}));
vi.mock('@/shared/api/context', () => ({ useApi: () => api }));
vi.mock('@/features/recording/capture/useRecorder', () => ({ useRecorder: () => recorder }));

describe('useTrackRecorder', () => {
  it('sube el WAV y crea el clip en la pista armada con la latencia compensada', async () => {
    const onOperation = vi.fn();
    const wav = new Uint8Array([1, 2, 3]);
    recorder.stop.mockResolvedValue(wav);
    api.upload.mockResolvedValue({ src: 'media/rec-001.wav', duration: 3 });
    const { result } = renderHook(() =>
      useTrackRecorder({ path: 'D:/editor/project.json', trackId: 't1', playhead: 5, recordOffsetMs: 10, deviceId: 'mic-1', onOperation }),
    );

    await act(() => result.current.start());
    await act(() => result.current.stop());

    expect(recorder.start).toHaveBeenCalledWith('mic-1');
    expect(api.upload).toHaveBeenCalledWith('/editor/projects/media?path=D%3A%2Feditor%2Fproject.json', wav, 'audio/wav');
    expect(onOperation).toHaveBeenCalledWith({
      type: 'addClip',
      clip: {
        id: expect.any(String), track: 't1', src: 'media/rec-001.wav', src_in: 0, src_out: 3,
        start: 4.963, gain_db: 0, fade_in: 0, fade_out: 0,
      },
    });
  });

  it('no graba si no hay una pista armada', async () => {
    const { result } = renderHook(() =>
      useTrackRecorder({ path: 'D:/editor/project.json', trackId: null, playhead: 0, recordOffsetMs: 0, onOperation: vi.fn() }),
    );

    await act(() => result.current.start());

    expect(recorder.start).not.toHaveBeenCalled();
    expect(result.current.error).toBe('editor.recorder.arm_track');
  });

  it('informa el error al iniciar y no intenta detener una captura que no comenzó', async () => {
    recorder.start.mockRejectedValueOnce(new Error('microphone unavailable'));
    const { result } = renderHook(() =>
      useTrackRecorder({ path: 'D:/editor/project.json', trackId: 't1', playhead: 0, recordOffsetMs: 0, onOperation: vi.fn() }),
    );

    await act(() => result.current.start());
    expect(result.current.error).toBe('editor.recorder.start_error');
    await act(() => result.current.stop());
    expect(recorder.stop).not.toHaveBeenCalled();
  });

  it('no sube una captura vacía y reporta el error si falla la subida', async () => {
    recorder.start.mockResolvedValue(undefined);
    recorder.stop.mockResolvedValueOnce(null).mockResolvedValueOnce(new Uint8Array([1]));
    api.upload.mockRejectedValueOnce(new Error('upload failed'));
    const { result } = renderHook(() =>
      useTrackRecorder({ path: 'D:/editor/project.json', trackId: 't1', playhead: 0, recordOffsetMs: 0, onOperation: vi.fn() }),
    );

    await act(() => result.current.start());
    await act(() => result.current.stop());
    expect(api.upload).not.toHaveBeenCalled();
    await act(() => result.current.start());
    await act(() => result.current.stop());
    expect(result.current.error).toBe('editor.recorder.upload_error');
  });

  it('conmuta entre iniciar y detener una captura activa', async () => {
    recorder.recording = false;
    recorder.start.mockResolvedValue(undefined);
    recorder.stop.mockResolvedValue(null);
    const { result, rerender } = renderHook(() =>
      useTrackRecorder({ path: 'D:/editor/project.json', trackId: 't1', playhead: 0, recordOffsetMs: 0, onOperation: vi.fn() }),
    );

    await act(() => result.current.toggle());
    expect(recorder.start).toHaveBeenCalledOnce();
    recorder.recording = true;
    rerender();
    await act(() => result.current.toggle());
    expect(recorder.stop).toHaveBeenCalledOnce();
  });
});

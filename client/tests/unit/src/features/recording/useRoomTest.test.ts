import { act, renderHook } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { useRoomTest } from '@/features/recording/useRoomTest';

beforeEach(() => {
  vi.useFakeTimers();
});

afterEach(() => {
  vi.useRealTimers();
});

describe('useRoomTest (spec 010, D-2)', () => {
  it('graba cinco segundos de silencio y da el ruido de fondo más alto que vio', () => {
    const recorder = { start: vi.fn().mockResolvedValue(undefined), stop: vi.fn().mockResolvedValue(null) };
    const { result, rerender } = renderHook(
      ({ rms }: { rms: number }) => useRoomTest({ ...recorder, levels: { peak: rms, rms } }),
      { initialProps: { rms: -60 } },
    );

    act(() => {
      result.current.run();
    });
    rerender({ rms: -42 });
    rerender({ rms: -55 });
    act(() => {
      vi.advanceTimersByTime(5000);
    });

    expect(recorder.start).toHaveBeenCalledTimes(1);
    expect(recorder.stop).toHaveBeenCalledTimes(1);
    expect(result.current.result).toEqual({ db: -42, noisy: true });
  });

  it('una sala por debajo de −50 dBFS no avisa de ruido', () => {
    const recorder = { start: vi.fn().mockResolvedValue(undefined), stop: vi.fn().mockResolvedValue(null) };
    const { result, rerender } = renderHook(
      ({ rms }: { rms: number }) => useRoomTest({ ...recorder, levels: { peak: rms, rms } }),
      { initialProps: { rms: -70 } },
    );

    act(() => {
      result.current.run();
    });
    rerender({ rms: -61 });
    act(() => {
      vi.advanceTimersByTime(5000);
    });

    expect(result.current.result).toEqual({ db: -61, noisy: false });
  });

  it('si el micrófono no abre, avisa y el temporizador no sigue', async () => {
    const recorder = { start: vi.fn().mockRejectedValue(new Error('NotAllowedError')), stop: vi.fn().mockResolvedValue(null) };
    const { result } = renderHook(() => useRoomTest({ ...recorder, levels: { peak: -60, rms: -60 } }));

    await act(async () => {
      result.current.run();
    });
    await act(async () => {
      vi.advanceTimersByTime(5000);
    });

    expect(result.current.failed).toBe(true);
    expect(result.current.running).toBe(false);
    expect(recorder.stop).not.toHaveBeenCalled();
  });

  it('con un micrófono elegido, la prueba de sala abre ese micrófono', () => {
    const recorder = { start: vi.fn().mockResolvedValue(undefined), stop: vi.fn().mockResolvedValue(null) };
    const { result } = renderHook(() => useRoomTest({ ...recorder, levels: { peak: -60, rms: -60 } }, 'mic-2'));

    act(() => {
      result.current.run();
    });

    expect(recorder.start).toHaveBeenCalledWith('mic-2');
  });

  it('no arranca otra prueba mientras una corre', () => {
    const recorder = { start: vi.fn().mockResolvedValue(undefined), stop: vi.fn().mockResolvedValue(null) };
    const { result } = renderHook(() => useRoomTest({ ...recorder, levels: { peak: -60, rms: -60 } }));

    act(() => {
      result.current.run();
    });
    act(() => {
      result.current.run();
    });

    expect(recorder.start).toHaveBeenCalledTimes(1);
  });
});

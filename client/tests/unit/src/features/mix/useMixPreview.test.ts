import { act, renderHook } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { applyCurve, useMixPreview } from '@/features/mix/useMixPreview';

/** Un AudioParam falso: anota cada rampa y cada cancelación, con su tiempo. */
function fakeGain() {
  const ramps: [number, number][] = [];
  const cancelled: number[] = [];
  const param = {
    linearRampToValueAtTime: (value: number, time: number) => ramps.push([value, time]),
    cancelScheduledValues: (time: number) => cancelled.push(time),
  } as unknown as AudioParam;
  return { param, ramps, cancelled };
}

function makeSource() {
  return { buffer: null, connect: vi.fn(), start: vi.fn(), stop: vi.fn() };
}

/** Un AudioContext falso: un GainNode con su AudioParam, y cada fuente que se crea. */
function fakeAudio() {
  const param = { cancelScheduledValues: vi.fn(), linearRampToValueAtTime: vi.fn() };
  const gain = { gain: param, connect: vi.fn() };
  const sources: ReturnType<typeof makeSource>[] = [];
  const context = {
    currentTime: 1,
    destination: {},
    createGain: () => gain,
    createBufferSource: () => {
      const source = makeSource();
      sources.push(source);
      return source;
    },
    decodeAudioData: vi.fn(async () => ({})),
    close: vi.fn(async () => undefined),
  };
  vi.stubGlobal('AudioContext', function AudioContextStub() {
    return context;
  });
  return { context, param, sources };
}

describe('applyCurve (AC-6: la vista previa)', () => {
  it('programa una rampa por cada punto, con los dB convertidos a ganancia y el tiempo desde el inicio', () => {
    const { param, ramps } = fakeGain();

    applyCurve(
      param,
      [
        [0, 0],
        [1, -12],
      ],
      10,
    );

    expect(ramps).toHaveLength(2);
    expect(ramps[0][1]).toBeCloseTo(10);
    expect(ramps[1][1]).toBeCloseTo(11);
    expect(ramps[1][0]).toBeCloseTo(10 ** (-12 / 20));
  });

  it('cancela lo programado desde el inicio antes de reprogramar, sin cortar lo que ya sonó', () => {
    const { param, cancelled } = fakeGain();

    applyCurve(param, [[0, 0]], 10);

    expect(cancelled).toEqual([10]);
  });
});

describe('useMixPreview (AC-6: reprograma la ganancia sin parar la reproducción)', () => {
  let audio: ReturnType<typeof fakeAudio>;

  beforeEach(() => {
    audio = fakeAudio();
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => ({ arrayBuffer: async () => new ArrayBuffer(4) })),
    );
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('arranca la música y la voz, y la voz entra después de la intro', async () => {
    const { result } = renderHook(() => useMixPreview([]));

    await act(async () => {
      await result.current.start('file://voz.wav', 'file://musica.wav', 2);
    });

    expect(result.current.active).toBe(true);
    expect(audio.context.decodeAudioData).toHaveBeenCalledTimes(2);
    expect(audio.sources[0].start.mock.calls[0][0]).toBeCloseTo(1.05);
    expect(audio.sources[1].start.mock.calls[0][0]).toBeCloseTo(3.05);
  });

  it('una curva nueva se reprograma sobre la ganancia que ya suena', async () => {
    const { result, rerender } = renderHook(({ curve }: { curve: [number, number][] }) => useMixPreview(curve), {
      initialProps: { curve: [] as [number, number][] },
    });
    await act(async () => {
      await result.current.start('file://voz.wav', 'file://musica.wav', 0);
    });

    rerender({
      curve: [
        [0, 0],
        [1, -12],
      ],
    });

    expect(audio.param.linearRampToValueAtTime).toHaveBeenCalledTimes(2);
  });

  it('parar detiene las fuentes, cierra el contexto y deja de estar activo', async () => {
    const { result } = renderHook(() => useMixPreview([]));
    await act(async () => {
      await result.current.start('file://voz.wav', 'file://musica.wav', 0);
    });

    act(() => {
      result.current.stop();
    });

    expect(result.current.active).toBe(false);
    expect(audio.sources[0].stop).toHaveBeenCalled();
    expect(audio.sources[1].stop).toHaveBeenCalled();
    expect(audio.context.close).toHaveBeenCalled();
  });

  it('parar una fuente que ya terminó no falla', async () => {
    const { result } = renderHook(() => useMixPreview([]));
    await act(async () => {
      await result.current.start('file://voz.wav', 'file://musica.wav', 0);
    });
    audio.sources[0].stop.mockImplementation(() => {
      throw new Error('InvalidStateNode');
    });

    act(() => {
      result.current.stop();
    });

    expect(result.current.active).toBe(false);
  });

  it('parar sin nada sonando no hace nada', () => {
    const { result } = renderHook(() => useMixPreview([]));

    act(() => {
      result.current.stop();
    });

    expect(result.current.active).toBe(false);
    expect(audio.context.close).not.toHaveBeenCalled();
  });
});

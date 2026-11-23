import { act, renderHook } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { usePlayback } from '@/features/editor/playback/usePlayback';
import type { Doc } from '@/features/editor/model/types';

const source = { connect: vi.fn(), disconnect: vi.fn() };
const gainParam = {
  cancelScheduledValues: vi.fn(),
  setValueAtTime: vi.fn(),
  linearRampToValueAtTime: vi.fn(),
};
const gain = { gain: gainParam, connect: vi.fn(), disconnect: vi.fn() };
const context = {
  currentTime: 0,
  destination: {},
  createMediaElementSource: vi.fn(() => source),
  createGain: vi.fn(() => gain),
  resume: vi.fn(async () => undefined),
  close: vi.fn(async () => undefined),
};
const elements: { src: string; currentTime: number; paused: boolean; seeking: boolean; play: ReturnType<typeof vi.fn>; pause: ReturnType<typeof vi.fn> }[] = [];
const frames: FrameRequestCallback[] = [];

const doc: Doc = {
  version: 1,
  name: 'preview',
  sample_rate: 48000,
  tracks: [{ id: 'voice', kind: 'audio', name: 'Voz', volume_db: -3, mute: false, solo: false, locked: false, height: 80 }],
  clips: [
    { id: 'voice-1', track: 'voice', src: 'D:/media/voice.wav', src_in: 2, src_out: 6, start: 0, gain_db: -3, fade_in: 0.5, fade_out: 0.5 },
  ],
  markers: [],
};

beforeEach(() => {
  vi.clearAllMocks();
  context.currentTime = 0;
  elements.length = 0;
  frames.length = 0;
  vi.stubGlobal('AudioContext', function AudioContextStub() { return context; });
  vi.stubGlobal('Audio', function AudioStub(src: string) {
    const element = {
      src,
      currentTime: 0,
      paused: true,
      seeking: false,
      play: vi.fn(async () => { element.paused = false; }),
      pause: vi.fn(() => { element.paused = true; }),
    };
    elements.push(element);
    return element;
  });
  vi.stubGlobal('requestAnimationFrame', vi.fn((callback: FrameRequestCallback) => {
    frames.push(callback);
    return frames.length;
  }));
  vi.stubGlobal('cancelAnimationFrame', vi.fn());
});

afterEach(() => vi.unstubAllGlobals());

describe('usePlayback', () => {
  it('crea un elemento por clip activo, enlaza su ganancia y reproduce la URL local', () => {
    const { result } = renderHook(() => usePlayback(doc, (path) => `http://local/files?path=${path}`));

    act(() => result.current.setPlaying(true));

    expect(result.current.playing).toBe(true);
    expect(elements).toHaveLength(1);
    expect(elements[0].src).toBe('http://local/files?path=D:/media/voice.wav');
    expect(elements[0].currentTime).toBe(2);
    expect(elements[0].play).toHaveBeenCalledOnce();
    expect(source.connect).toHaveBeenCalledWith(gain);
    expect(gain.connect).toHaveBeenCalledWith(context.destination);
    expect(gainParam.linearRampToValueAtTime).toHaveBeenCalledTimes(3);
  });

  it('prepara el clip dentro de la ventana y reproduce al llegar a su inicio', () => {
    const delayed: Doc = { ...doc, clips: [{ ...doc.clips[0], start: 1 }] };
    const { result } = renderHook(() => usePlayback(delayed, (path) => path));
    act(() => result.current.setPlaying(true));
    expect(elements).toHaveLength(1);
    expect(elements[0].currentTime).toBe(2);
    expect(elements[0].play).not.toHaveBeenCalled();

    context.currentTime = 1;
    act(() => frames.shift()?.(0));
    expect(elements).toHaveLength(1);
    expect(elements[0].currentTime).toBe(2);
    expect(elements[0].play).toHaveBeenCalledOnce();
    expect(result.current.position).toBe(1);
  });

  it('corrige una deriva de más de 40 ms usando el reloj del contexto', () => {
    const { result } = renderHook(() => usePlayback(doc, (path) => path));
    act(() => result.current.setPlaying(true));
    elements[0].currentTime = 2.8;
    context.currentTime = 1;

    act(() => frames.shift()?.(0));

    expect(elements[0].currentTime).toBe(3);
    expect(result.current.position).toBe(1);
  });

  it('no busca el medio mientras está en curso otra búsqueda', () => {
    const { result } = renderHook(() => usePlayback(doc, (path) => path));
    act(() => result.current.setPlaying(true));
    elements[0].seeking = true;
    elements[0].currentTime = 2.5;
    context.currentTime = 1;

    act(() => frames.shift()?.(0));

    expect(elements[0].currentTime).toBe(2.5);
  });

  it('busca una posición nueva y reprograma la ganancia si cambia el proyecto', () => {
    const { result, rerender } = renderHook(({ value }: { value: Doc }) => usePlayback(value, (path) => path), {
      initialProps: { value: doc },
    });
    act(() => result.current.setPlaying(true));
    act(() => result.current.seek(1));
    expect(elements[0].currentTime).toBe(3);

    rerender({ value: { ...doc, tracks: [{ ...doc.tracks[0], volume_db: -9 }] } });
    context.currentTime = 0.1;
    act(() => frames.shift()?.(0));

    expect(gainParam.cancelScheduledValues).toHaveBeenCalledTimes(3);
    expect(result.current.position).toBe(1.1);
  });

  it('detiene la reproducción al llegar al final y libera clips inactivos', () => {
    const { result } = renderHook(() => usePlayback(doc, (path) => path));
    act(() => result.current.setPlaying(true));
    context.currentTime = 4;

    act(() => frames.shift()?.(0));

    expect(result.current.position).toBe(4);
    expect(result.current.playing).toBe(false);
    expect(elements[0].pause).toHaveBeenCalled();
    expect(source.disconnect).toHaveBeenCalled();
  });

  it('ignora la solicitud repetida del mismo estado', () => {
    const { result } = renderHook(() => usePlayback(doc, (path) => path));
    act(() => result.current.setPlaying(true));
    act(() => result.current.setPlaying(true));

    expect(context.resume).toHaveBeenCalledOnce();
    expect(elements).toHaveLength(1);
  });

  it('pausa los elementos y stop vuelve al inicio', () => {
    const { result } = renderHook(() => usePlayback(doc, (path) => path));
    act(() => result.current.setPlaying(true));
    act(() => result.current.setPlaying(false));
    expect(elements[0].pause).toHaveBeenCalled();

    act(() => result.current.stop());
    expect(result.current.position).toBe(0);
    expect(result.current.playing).toBe(false);
  });

  it('libera los elementos y cierra el contexto al desmontar', () => {
    const { result, unmount } = renderHook(() => usePlayback(doc, (path) => path));
    act(() => result.current.setPlaying(true));
    unmount();
    expect(elements[0].pause).toHaveBeenCalled();
    expect(source.disconnect).toHaveBeenCalled();
    expect(gain.disconnect).toHaveBeenCalled();
    expect(context.close).toHaveBeenCalledOnce();
  });
});

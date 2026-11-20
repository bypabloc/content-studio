import { act, cleanup, renderHook, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { useRecorder } from '@/features/recording/capture/useRecorder';

const { stopTrack, closeContext, getUserMedia } = vi.hoisted(() => ({
  stopTrack: vi.fn(),
  closeContext: vi.fn(),
  getUserMedia: vi.fn(),
}));

// AudioContext y el worklet no existen en jsdom: se simulan lo justo para el arranque y la parada.
class FakeAudioContext {
  static created: { options: AudioContextOptions | undefined }[] = [];
  sampleRate = 48000;
  audioWorklet = { addModule: vi.fn().mockResolvedValue(undefined) };
  constructor(options?: AudioContextOptions) {
    FakeAudioContext.created.push({ options });
  }
  createMediaStreamSource() {
    return { connect: vi.fn(), disconnect: vi.fn() };
  }
  createAnalyser() {
    return { fftSize: 2048, connect: vi.fn(), disconnect: vi.fn(), getFloatTimeDomainData: vi.fn() };
  }
  // El worklet se conecta a una ganancia de 0 y de ahí al destino: así el navegador lo procesa sin sonar.
  createGain() {
    return { gain: { value: 1 }, connect: vi.fn(), disconnect: vi.fn() };
  }
  destination = {};
  close() {
    closeContext();
    return Promise.resolve();
  }
}

class FakeWorkletNode {
  static last: FakeWorkletNode | undefined;
  port = { onmessage: null as ((event: MessageEvent) => void) | null, postMessage: vi.fn() };
  connect = vi.fn();
  disconnect = vi.fn();
  constructor() {
    FakeWorkletNode.last = this;
  }
}

beforeEach(() => {
  getUserMedia.mockResolvedValue({
    getTracks: () => [{ stop: stopTrack, getSettings: () => ({ sampleRate: 48000 }) }],
  });
  Object.defineProperty(navigator, 'mediaDevices', { value: { getUserMedia }, configurable: true });
  vi.stubGlobal('AudioContext', FakeAudioContext);
  vi.stubGlobal('AudioWorkletNode', FakeWorkletNode);
});

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  vi.clearAllMocks();
  FakeAudioContext.created = [];
});

describe('useRecorder', () => {
  it('AC-3 (D-2): pide el micrófono sin procesado, mono y a 48 kHz', async () => {
    const { result } = renderHook(() => useRecorder());

    await act(() => result.current.start('mic-1'));

    expect(getUserMedia).toHaveBeenCalledWith({
      audio: {
        deviceId: 'mic-1',
        channelCount: 1,
        sampleRate: 48000,
        echoCancellation: false,
        noiseSuppression: false,
        autoGainControl: false,
      },
    });
  });

  it('abre el contexto a 48 kHz y deja el valor que dio el dispositivo', async () => {
    const { result } = renderHook(() => useRecorder());

    await act(() => result.current.start());

    expect(FakeAudioContext.created[0].options).toEqual({ sampleRate: 48000 });
    expect(result.current.sampleRate).toBe(48000);
    expect(result.current.recording).toBe(true);
  });

  it('parar suelta el micrófono, cierra el contexto y devuelve un WAV', async () => {
    const { result } = renderHook(() => useRecorder());
    await act(() => result.current.start());

    let wav: Uint8Array | null | undefined;
    await act(async () => {
      wav = await result.current.stop();
    });

    expect(stopTrack).toHaveBeenCalled();
    expect(closeContext).toHaveBeenCalled();
    expect(result.current.recording).toBe(false);
    expect(new TextDecoder().decode(wav?.subarray(0, 4))).toBe('RIFF');
  });

  it('mientras graba, el nivel sale de los bloques del worklet: pico y RMS en dBFS', async () => {
    const { result } = renderHook(() => useRecorder());
    await act(() => result.current.start());

    act(() => FakeWorkletNode.last?.port.onmessage?.({ data: new Float32Array(128).fill(0.5) } as MessageEvent));

    await waitFor(() => expect(result.current.levels.peak).toBeCloseTo(-6.02, 1));
    expect(result.current.levels.rms).toBeCloseTo(-6.02, 1);
  });

  it('parar sin haber grabado no devuelve nada ni toca el micrófono', async () => {
    const { result } = renderHook(() => useRecorder());

    let wav: Uint8Array | null | undefined;
    await act(async () => {
      wav = await result.current.stop();
    });

    expect(wav).toBeNull();
    expect(closeContext).not.toHaveBeenCalled();
  });

  it('si el dispositivo no informa su frecuencia, vale la del contexto', async () => {
    getUserMedia.mockResolvedValueOnce({ getTracks: () => [] });
    const { result } = renderHook(() => useRecorder());

    await act(() => result.current.start());

    expect(result.current.sampleRate).toBe(48000);
  });
});

import { afterEach, describe, expect, it, vi } from 'vitest';

interface Worklet {
  port: { postMessage: ReturnType<typeof vi.fn> };
  process(inputs: Float32Array[][]): boolean;
}

afterEach(() => {
  vi.unstubAllGlobals();
  vi.resetModules();
});

// El worklet corre en el hilo de audio: aquí se carga con una clase base y un `registerProcessor` falsos.
async function loadWorklet(): Promise<new () => Worklet> {
  const registry: { name?: string; processor?: new () => Worklet } = {};
  class FakeProcessor {
    port = { postMessage: vi.fn() };
  }
  vi.stubGlobal('AudioWorkletProcessor', FakeProcessor);
  vi.stubGlobal('registerProcessor', (name: string, processor: new () => Worklet) => {
    registry.name = name;
    registry.processor = processor;
  });
  await import('@/features/recording/capture/recorder-worklet');
  expect(registry.name).toBe('recorder');
  if (!registry.processor) throw new Error('el worklet no se registró');
  return registry.processor;
}

describe('recorder-worklet', () => {
  it('manda cada bloque al hilo principal como una copia', async () => {
    const Processor = await loadWorklet();
    const worklet = new Processor();
    const block = Float32Array.from([0.25, -0.5]);

    expect(worklet.process([[block]])).toBe(true);
    block[0] = 0.9; // el hilo de audio reutiliza el bloque: lo enviado no debe cambiar

    expect(worklet.port.postMessage).toHaveBeenCalledTimes(1);
    expect(worklet.port.postMessage.mock.calls[0][0]).toEqual(Float32Array.from([0.25, -0.5]));
  });

  it('sin canal de entrada no envía nada y sigue vivo', async () => {
    const Processor = await loadWorklet();
    const worklet = new Processor();

    expect(worklet.process([])).toBe(true);
    expect(worklet.port.postMessage).not.toHaveBeenCalled();
  });
});

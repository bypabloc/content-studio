import { afterEach, describe, expect, it, vi } from 'vitest';
import { ding } from '@/shared/notify/ding';

describe('ding', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('suena 0,15 s con un oscilador que se apaga solo', () => {
    const oscillator = { frequency: { value: 0 }, connect: vi.fn(() => oscillator), start: vi.fn(), stop: vi.fn() };
    const gain = { gain: { setValueAtTime: vi.fn(), exponentialRampToValueAtTime: vi.fn() }, connect: vi.fn(() => gain) };
    const context = {
      currentTime: 1,
      destination: {},
      createOscillator: vi.fn(() => oscillator),
      createGain: vi.fn(() => gain),
    };
    // `new AudioContext()` necesita un constructor; devolver el objeto desde él hace de contexto de prueba.
    vi.stubGlobal(
      'AudioContext',
      vi.fn(function audioContext() {
        return context;
      }),
    );

    ding();

    expect(oscillator.frequency.value).toBe(880);
    expect(oscillator.start).toHaveBeenCalledOnce();
    expect(oscillator.stop).toHaveBeenCalledWith(1.15);
  });
});

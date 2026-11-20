import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';
import { encodeWav } from '@/features/recording/capture/encodeWav';

const RATE = 48000;
// Huella de los bytes que escribe `encodeWav` para esta senoidal: la fija `scripts/wav-fixture.ts` y la lee el server.
// Vitest corre desde client/ (`bun run --cwd client test`), así que la ruta sale desde ahí.
const GOLDEN = resolve(process.cwd(), '../server/tests/fixtures/voices/client-sine-1s-48k-24b.sha256');

function sine(samples: number, amplitude = 1, hz = 1000): Float32Array {
  return Float32Array.from({ length: samples }, (_, i) => amplitude * Math.sin((2 * Math.PI * hz * i) / RATE));
}

function ascii(bytes: Uint8Array, from: number, length: number): string {
  return String.fromCharCode(...bytes.subarray(from, from + length));
}

function view(bytes: Uint8Array): DataView {
  return new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
}

describe('encodeWav', () => {
  it('AC-3: 48.000 muestras de una senoidal dan un WAV de 1,0 s, mono, 48 kHz y 24 bits', () => {
    const wav = encodeWav(sine(RATE), RATE, 24);
    const dv = view(wav);

    expect(wav.byteLength).toBe(44 + RATE * 3);
    expect(ascii(wav, 0, 4)).toBe('RIFF');
    expect(dv.getUint32(4, true)).toBe(wav.byteLength - 8);
    expect(ascii(wav, 8, 4)).toBe('WAVE');
    expect(ascii(wav, 12, 4)).toBe('fmt ');
    expect(dv.getUint32(16, true)).toBe(16);
    expect(dv.getUint16(20, true)).toBe(1);
    expect(dv.getUint16(22, true)).toBe(1);
    expect(dv.getUint32(24, true)).toBe(RATE);
    expect(dv.getUint32(28, true)).toBe(RATE * 3);
    expect(dv.getUint16(32, true)).toBe(3);
    expect(dv.getUint16(34, true)).toBe(24);
    expect(ascii(wav, 36, 4)).toBe('data');
    expect(dv.getUint32(40, true)).toBe(RATE * 3);
  });

  it('escribe cada muestra en 24 bits con signo, little-endian, y recorta lo que pasa de 1', () => {
    const wav = encodeWav(Float32Array.from([1, -1, 0, 2]), RATE, 24);
    const dv = view(wav);
    const sample = (i: number) => {
      const at = 44 + i * 3;
      const raw = dv.getUint8(at) | (dv.getUint8(at + 1) << 8) | (dv.getUint8(at + 2) << 16);
      return (raw << 8) >> 8; // extiende el signo de 24 bits
    };

    expect(sample(0)).toBe(0x7fffff);
    expect(sample(1)).toBe(-0x800000);
    expect(sample(2)).toBe(0);
    expect(sample(3)).toBe(0x7fffff);
  });

  it('AC-3: los bytes tienen la huella que el server reconstruye y lee con ffprobe', () => {
    const digest = createHash('sha256').update(encodeWav(sine(RATE), RATE, 24)).digest('hex');

    expect(digest).toBe(readFileSync(GOLDEN, 'utf8').trim());
  });
});

/** WAV PCM mono de 24 bits (spec 010, D-2): cabecera RIFF de 44 bytes y muestras con signo, little-endian. */

const HEADER_SIZE = 44;
const BYTES_PER_SAMPLE = 3; // 24 bits

function writeAscii(out: Uint8Array, at: number, text: string): void {
  for (let i = 0; i < text.length; i++) out[at + i] = text.charCodeAt(i);
}

/** Codifica muestras en -1..1 como WAV de 24 bits; lo que pasa de 1 en valor absoluto se recorta. */
export function encodeWav(samples: Float32Array, sampleRate: number, bits: 24): Uint8Array {
  const dataSize = samples.length * BYTES_PER_SAMPLE;
  const out = new Uint8Array(HEADER_SIZE + dataSize);
  const view = new DataView(out.buffer);
  writeAscii(out, 0, 'RIFF');
  view.setUint32(4, HEADER_SIZE - 8 + dataSize, true);
  writeAscii(out, 8, 'WAVE');
  writeAscii(out, 12, 'fmt ');
  view.setUint32(16, 16, true); // tamaño del bloque fmt
  view.setUint16(20, 1, true); // PCM
  view.setUint16(22, 1, true); // mono
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, sampleRate * BYTES_PER_SAMPLE, true);
  view.setUint16(32, BYTES_PER_SAMPLE, true);
  view.setUint16(34, bits, true);
  writeAscii(out, 36, 'data');
  view.setUint32(40, dataSize, true);
  for (let i = 0; i < samples.length; i++) {
    const x = Math.max(-1, Math.min(1, samples[i]));
    const value = Math.round(x < 0 ? x * 0x800000 : x * 0x7fffff);
    const at = HEADER_SIZE + i * BYTES_PER_SAMPLE;
    out[at] = value & 0xff;
    out[at + 1] = (value >> 8) & 0xff;
    out[at + 2] = (value >> 16) & 0xff;
  }
  return out;
}

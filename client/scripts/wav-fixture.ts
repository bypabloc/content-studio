// Fija la huella (SHA-256) del WAV de una senoidal de 1 s que escribe `encodeWav`. El client la comprueba en su
// prueba; el server reconstruye ese mismo WAV en Python, comprueba la huella y lo lee con ffprobe (test_ffmpeg.py).
// No se versiona audio: la guarda de staging lo rechaza, y la huella basta para unir los dos lados.
// Uso, desde client/: bun scripts/wav-fixture.ts. Solo cambia si cambia el formato del WAV.
import { createHash } from 'node:crypto';
import { mkdirSync, writeFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { encodeWav } from '../src/features/recording/capture/encodeWav';

const RATE = 48000;
const samples = Float32Array.from({ length: RATE }, (_, i) => Math.sin((2 * Math.PI * 1000 * i) / RATE));
const digest = createHash('sha256').update(encodeWav(samples, RATE, 24)).digest('hex');
const target = resolve('../server/tests/fixtures/voices/client-sine-1s-48k-24b.sha256');

mkdirSync(dirname(target), { recursive: true });
writeFileSync(target, `${digest}\n`);
console.error(`wrote ${target}: ${digest}`);

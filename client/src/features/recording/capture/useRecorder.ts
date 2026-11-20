import { useCallback, useEffect, useRef, useState } from 'react';
import { encodeWav } from '@/features/recording/capture/encodeWav';
import { FLOOR_DBFS, peakDbfs, rmsDbfs } from '@/features/recording/capture/levels';
// Vite resuelve `?worker&url` a la URL del módulo; oxlint no conoce ese sufijo y lo marca como import sin default.
// oxlint-disable-next-line import/default
import workletUrl from '@/features/recording/capture/recorder-worklet.ts?worker&url';

// D-2: 48 kHz, sin procesado. Si el dispositivo no da 48 kHz, `sampleRate` lo dice y el server la convierte a 48 kHz.
const RATE = 48000;
const LEVEL_EVERY_MS = 100; // los niveles se pintan a 10 Hz, no por cada bloque de 128 muestras

export interface Levels {
  peak: number;
  rms: number;
}

interface Session {
  stream: MediaStream;
  context: AudioContext;
  chunks: Float32Array[];
  timer: ReturnType<typeof setInterval>;
}

const SILENCE: Levels = { peak: FLOOR_DBFS, rms: FLOOR_DBFS };

function concat(chunks: Float32Array[]): Float32Array {
  const out = new Float32Array(chunks.reduce((n, chunk) => n + chunk.length, 0));
  let at = 0;
  for (const chunk of chunks) {
    out.set(chunk, at);
    at += chunk.length;
  }
  return out;
}

/** Graba el micrófono con un AudioWorklet: `start` lo abre, `stop` lo suelta y devuelve el WAV de 24 bits. */
export function useRecorder() {
  const [recording, setRecording] = useState(false);
  const [sampleRate, setSampleRate] = useState<number | null>(null);
  const [levels, setLevels] = useState<Levels>(SILENCE);
  const current = useRef<Session | null>(null);

  const finish = useCallback(async () => {
    const session = current.current;
    if (!session) return null;
    current.current = null;
    clearInterval(session.timer);
    session.stream.getTracks().forEach((track) => track.stop());
    await session.context.close();
    return { samples: concat(session.chunks), rate: session.context.sampleRate };
  }, []);

  const start = useCallback(async (deviceId?: string) => {
    const stream = await navigator.mediaDevices.getUserMedia({
      audio: {
        deviceId,
        channelCount: 1,
        sampleRate: RATE,
        echoCancellation: false,
        noiseSuppression: false,
        autoGainControl: false,
      },
    });
    const context = new AudioContext({ sampleRate: RATE });
    await context.audioWorklet.addModule(workletUrl);
    const chunks: Float32Array[] = [];
    let last = SILENCE;
    const node = new AudioWorkletNode(context, 'recorder');
    node.port.onmessage = (event: MessageEvent<Float32Array>) => {
      chunks.push(event.data);
      last = { peak: peakDbfs(event.data), rms: rmsDbfs(event.data) };
    };
    const mute = context.createGain();
    mute.gain.value = 0;
    context.createMediaStreamSource(stream).connect(node);
    node.connect(mute);
    mute.connect(context.destination);
    const timer = setInterval(() => setLevels(last), LEVEL_EVERY_MS);
    current.current = { stream, context, chunks, timer };
    setSampleRate(stream.getTracks()[0]?.getSettings().sampleRate ?? context.sampleRate);
    setRecording(true);
  }, []);

  const stop = useCallback(async (): Promise<Uint8Array | null> => {
    const done = await finish();
    setRecording(false);
    setLevels(SILENCE);
    return done ? encodeWav(done.samples, done.rate, 24) : null;
  }, [finish]);

  // Si la pantalla se cierra grabando, se suelta el micrófono.
  useEffect(() => () => void finish(), [finish]);

  return { recording, sampleRate, levels, start, stop };
}

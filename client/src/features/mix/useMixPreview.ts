import { useCallback, useEffect, useRef, useState } from 'react';

/**
 * Pone la curva de ducking en la ganancia de la música: una rampa lineal por punto (dB convertidos a ganancia), contada
 * desde `offset`, el instante en que empezó la reproducción (spec 016, D-3). Cancela lo programado desde ahí, así que
 * volver a programar no corta lo que ya suena.
 */
export function applyCurve(param: AudioParam, curve: [number, number][], offset: number): void {
  param.cancelScheduledValues(offset);
  for (const [t, db] of curve) {
    param.linearRampToValueAtTime(10 ** (db / 20), offset + t);
  }
}

interface Playback {
  context: AudioContext;
  gain: GainNode;
  sources: AudioBufferSourceNode[];
  started: number;
}

async function decode(context: AudioContext, url: string): Promise<AudioBuffer> {
  const response = await fetch(url);
  return context.decodeAudioData(await response.arrayBuffer());
}

/**
 * La vista previa de la mezcla con WebAudio (D-4): la voz y la música decodificadas desde `/files`, y la ganancia de la
 * música con la curva del server. Cuando la curva cambia, vuelve a programar sin parar la reproducción (AC-6).
 */
export function useMixPreview(curve: [number, number][]): {
  active: boolean;
  start: (voiceUrl: string, musicUrl: string, intro: number) => Promise<void>;
  stop: () => void;
} {
  const playback = useRef<Playback | null>(null);
  const [active, setActive] = useState(false);

  useEffect(() => {
    const current = playback.current;
    if (current) applyCurve(current.gain.gain, curve, current.started);
  }, [curve]);

  const stop = useCallback(() => {
    const current = playback.current;
    if (!current) return;
    for (const source of current.sources) {
      try {
        source.stop();
      } catch {
        // Una fuente que ya terminó no se puede parar otra vez: no pasa nada.
      }
    }
    void current.context.close();
    playback.current = null;
    setActive(false);
  }, []);

  const start = useCallback(
    async (voiceUrl: string, musicUrl: string, intro: number) => {
      stop();
      const context = new AudioContext();
      const [voice, music] = await Promise.all([decode(context, voiceUrl), decode(context, musicUrl)]);
      const gain = context.createGain();
      gain.connect(context.destination);
      const musicSource = context.createBufferSource();
      musicSource.buffer = music;
      musicSource.connect(gain);
      const voiceSource = context.createBufferSource();
      voiceSource.buffer = voice;
      voiceSource.connect(context.destination);
      const started = context.currentTime + 0.05;
      applyCurve(gain.gain, curve, started);
      musicSource.start(started);
      voiceSource.start(started + intro);
      playback.current = { context, gain, sources: [musicSource, voiceSource], started };
      setActive(true);
    },
    [curve, stop],
  );

  return { active, start, stop };
}

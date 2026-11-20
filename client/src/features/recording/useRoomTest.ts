import { useEffect, useRef, useState } from 'react';
import type { Levels } from './capture/useRecorder';

// La prueba de sala graba cinco segundos de silencio (spec 010, D-2).
export const ROOM_MS = 5000;
// Más ruido de fondo que esto es una sala ruidosa. Es el mismo límite del chequeo de tomas (`voice_check.NOISE_MAX`).
export const NOISE_MAX = -50;

export interface RoomRecorder {
  start: (deviceId?: string) => Promise<void>;
  stop: () => Promise<Uint8Array | null>;
  levels: Levels;
}

export interface RoomResult {
  db: number;
  noisy: boolean;
}

/**
 * Graba cinco segundos de silencio con el micrófono elegido (o el predeterminado) y da el ruido de fondo más alto que llegó.
 * El audio se descarta: la prueba solo mide. Si el micrófono no abre, `failed` lo dice y el temporizador no queda corriendo.
 */
export function useRoomTest(recorder: RoomRecorder, deviceId?: string) {
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<RoomResult | null>(null);
  const [failed, setFailed] = useState(false);
  const loudest = useRef(Number.NEGATIVE_INFINITY);
  const timer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
  const { rms } = recorder.levels;

  // Mientras la prueba corre, guarda el RMS más alto que llega.
  useEffect(() => {
    if (running) loudest.current = Math.max(loudest.current, rms);
  }, [running, rms]);

  // Si la pantalla se cierra en mitad de la prueba, el temporizador no sigue.
  useEffect(() => () => clearTimeout(timer.current), []);

  const run = () => {
    if (running) return;
    loudest.current = Number.NEGATIVE_INFINITY;
    setResult(null);
    setFailed(false);
    setRunning(true);
    timer.current = setTimeout(() => {
      void recorder.stop();
      const db = loudest.current;
      setRunning(false);
      setResult({ db, noisy: db > NOISE_MAX });
    }, ROOM_MS);
    recorder.start(deviceId).catch(() => {
      clearTimeout(timer.current);
      setRunning(false);
      setFailed(true);
    });
  };

  return { running, result, failed, run };
}

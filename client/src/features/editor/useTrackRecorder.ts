import { useCallback, useRef, useState } from 'react';

import { useRecorder } from '@/features/recording/capture/useRecorder';
import { useApi } from '@/shared/api/context';

import type { Op } from './model/types';

type Params = {
  path: string;
  trackId: string | null;
  playhead: number;
  recordOffsetMs: number;
  deviceId?: string;
  onOperation: (op: Op) => void;
};

type UploadedRecording = { src: string; duration: number };
type Started = { trackId: string; playhead: number };

/** Captura una toma, la sube al proyecto y crea el clip alineado con el cabezal. */
export function useTrackRecorder({ path, trackId, playhead, recordOffsetMs, deviceId, onOperation }: Params) {
  const api = useApi();
  const recorder = useRecorder();
  const startRecording = recorder.start;
  const stopRecording = recorder.stop;
  const recording = recorder.recording;
  const levels = recorder.levels;
  const latencyMs = recorder.latencyMs;
  const started = useRef<Started | null>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const start = useCallback(async () => {
    setError(null);
    if (!trackId) {
      setError('editor.recorder.arm_track');
      return;
    }
    started.current = { trackId, playhead };
    try {
      await startRecording(deviceId);
    } catch {
      started.current = null;
      setError('editor.recorder.start_error');
    }
  }, [deviceId, playhead, startRecording, trackId]);

  const stop = useCallback(async () => {
    const session = started.current;
    if (!session) return;
    const wav = await stopRecording();
    started.current = null;
    if (!wav) return;
    setUploading(true);
    setError(null);
    try {
      const query = `?path=${encodeURIComponent(path)}`;
      const saved = await api.upload<UploadedRecording>(`/editor/projects/media${query}`, wav, 'audio/wav');
      const latency = (latencyMs + recordOffsetMs) / 1000;
      onOperation({
        type: 'addClip',
        clip: {
          id: crypto.randomUUID(),
          track: session.trackId,
          src: saved.src,
          src_in: 0,
          src_out: saved.duration,
          start: Math.max(0, session.playhead - latency),
          gain_db: 0,
          fade_in: 0,
          fade_out: 0,
        },
      });
    } catch {
      setError('editor.recorder.upload_error');
    } finally {
      setUploading(false);
    }
  }, [api, latencyMs, onOperation, path, recordOffsetMs, stopRecording]);

  return {
    recording,
    levels,
    latencyMs,
    uploading,
    error,
    start,
    stop,
    toggle: () => void (recording ? stop() : start()),
  };
}

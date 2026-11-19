import { useQuery } from '@tanstack/react-query';
import { useApi } from '@/shared/api/context';
import type { components } from '@/shared/api/schema';
import { useMediaInfo, useMediaPeaks } from '@/shared/media/useMediaInfo';

export type Job = components['schemas']['Job'];

/** `script.json` de la carpeta de un trabajo: el nombre de su .wav y los párrafos tal como se pidieron (D-2). */
export interface Script {
  wav: string;
  segments: { text: string }[];
}

/** El `.json` de la toma (`save_metadata`): la semilla, la duración y la evaluación de whisper, o null si no se evaluó. */
export interface Take {
  seed: number;
  duration_s: number;
  evaluation: { rounds: number; ok: boolean; observations: string[] } | null;
}

/**
 * Los datos de una toma, leídos de la carpeta del trabajo: su guion (`script.json`), su `.json` (semilla, duración y
 * evaluación), su volumen y su onda. Sin carpeta de salida no pide nada.
 */
export function useTake(job: Job) {
  const api = useApi();
  const folder = job.output_dir ?? '';
  const inFolder = (name: string) => `${folder}/${name}`;
  const script = useQuery({
    queryKey: ['takes', folder, 'script'],
    queryFn: () => api.get<Script>(`/files?path=${encodeURIComponent(inFolder('script.json'))}`),
    enabled: folder !== '',
  });
  const wav = script.data ? inFolder(script.data.wav) : '';
  const take = useQuery({
    queryKey: ['takes', wav, 'json'],
    queryFn: () => api.get<Take>(`/files?path=${encodeURIComponent(wav.replace(/\.wav$/, '.json'))}`),
    enabled: wav !== '',
  });
  return { wav, script, take, info: useMediaInfo(wav), peaks: useMediaPeaks(wav) };
}

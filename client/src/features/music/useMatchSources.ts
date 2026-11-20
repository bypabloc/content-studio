import { useQueries, useQuery } from '@tanstack/react-query';

import { useApi } from '@/shared/api/context';
import type { components } from '@/shared/api/schema';

import type { MatchSource } from './DurationField';

type Job = components['schemas']['Job'];

/** Nombre visible de una narración: su texto, o su número si no tiene texto (una lista de archivos). */
function labelOf(job: Job): string {
  const text = job.params.text;
  return typeof text === 'string' && text.trim() !== '' ? text.slice(0, 40) : `#${job.id}`;
}

/**
 * Las narraciones terminadas con su duración real, ★ primero (spec 011, D-4). El .wav sale de `script.json` de la
 * carpeta del trabajo y su duración de `/media/info`. Sin carpeta de salida no entra en la lista.
 */
export function useMatchSources(): MatchSource[] {
  const api = useApi();
  const done = useQuery({
    queryKey: ['jobs', 'narration', 'done'],
    queryFn: () => api.get<Job[]>('/jobs?kind=narration&status=done'),
  });
  const withFolder = (done.data ?? []).filter((job) => job.output_dir);
  const durations = useQueries({
    queries: withFolder.map((job) => ({
      queryKey: ['music', 'match', job.id],
      queryFn: async () => {
        const script = await api.get<{ wav: string }>(`/files?path=${encodeURIComponent(`${job.output_dir}/script.json`)}`);
        const info = await api.get<{ duration: number }>(
          `/media/info?path=${encodeURIComponent(`${job.output_dir}/${script.wav}`)}`,
        );
        return info.duration;
      },
    })),
  });
  return withFolder
    .map((job, index) => ({
      id: String(job.id),
      label: labelOf(job),
      starred: job.starred,
      duration: durations[index]?.data,
    }))
    .filter((source): source is MatchSource => source.duration !== undefined)
    .sort((a, b) => Number(b.starred) - Number(a.starred));
}

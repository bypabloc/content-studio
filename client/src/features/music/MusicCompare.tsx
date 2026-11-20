import { useMutation, useQueries, useQuery, useQueryClient } from '@tanstack/react-query';

import { useApi } from '@/shared/api/context';
import type { components } from '@/shared/api/schema';
import { UIButton } from '@/shared/components/atoms/UIButton';
import { UIStack } from '@/shared/components/atoms/UIStack';
import { UIText } from '@/shared/components/atoms/UIText';
import { label, t } from '@/shared/i18n/t';
import { Player } from '@/shared/media/Player';
import { useMediaPeaks } from '@/shared/media/useMediaInfo';

type Job = components['schemas']['Job'];

/** Una pista del `tracks.json` de su trabajo (spec 011, D-6). */
export interface Track {
  file: string;
  style: string;
  variant: number;
  requested: number;
  duration: number;
  warning: string | null;
  voice: boolean | null;
  lufs: number;
  key: string | null;
  bpm: number | null;
}

interface Manifest {
  tracks: Track[];
  chosen: string | null;
}

interface Row {
  job: Job;
  track: Track;
  chosen: boolean;
}

/** Las pistas de los trabajos terminados del grupo, con su marca de elegida. */
function useRows(groupKey: string): Row[] {
  const api = useApi();
  const group = useQuery({
    queryKey: ['jobs', 'group', groupKey],
    queryFn: () => api.get<Job[]>(`/jobs?group_key=${encodeURIComponent(groupKey)}`),
  });
  const done = (group.data ?? []).filter((job) => job.status === 'done' && job.output_dir);
  const manifests = useQueries({
    queries: done.map((job) => ({
      queryKey: ['music', 'tracks', job.id],
      queryFn: () => api.get<Manifest>(`/files?path=${encodeURIComponent(`${job.output_dir}/tracks.json`)}`),
    })),
  });
  return done.flatMap((job, index) => {
    const manifest = manifests[index]?.data;
    return (manifest?.tracks ?? []).map((track) => ({ job, track, chosen: manifest?.chosen === track.file }));
  });
}

function voiceText(voice: boolean | null): string {
  if (voice === null) return t('music.compare.voice.unknown');
  return voice ? t('music.compare.voice.yes') : t('music.compare.voice.no');
}

/** La onda y el reproductor de una pista (solo cuando su archivo ya existe). */
function TrackPlayer({ path }: { path: string }): React.JSX.Element | null {
  const api = useApi();
  const peaks = useMediaPeaks(path);
  return peaks.data ? <Player src={api.fileUrl(path)} peaks={peaks.data.peaks} /> : null;
}

/**
 * Comparar las pistas de un pedido (spec 011, D-6): duración real, aviso, voz, volumen, tonalidad y BPM. «Elegir» marca
 * una pista y deja una sola elegida por grupo. «Mandar a Mezclar» llega con la 016 y por ahora queda deshabilitado.
 */
export function MusicCompare({ groupKey }: { groupKey: string }): React.JSX.Element {
  const api = useApi();
  const queryClient = useQueryClient();
  const rows = useRows(groupKey);
  const choose = useMutation({
    mutationFn: (row: Row) => api.post(`/jobs/${row.job.id}/choose`, { file: row.track.file }),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ['music', 'tracks'] }),
  });

  if (rows.length === 0) return <UIText variant="caption">{t('music.compare.empty')}</UIText>;
  return (
    <UIStack gap="md">
      {rows.map((row) => (
        <UIStack key={`${row.job.id}:${row.track.file}`} gap="xs" className="rounded-md border p-3" data-track={row.track.file}>
          <UIStack direction="row" gap="md" align="center" className="flex-wrap">
            <UIText>{label('music.style', row.track.style)}</UIText>
            <UIText variant="caption">{`${t('music.compare.variant')} ${row.track.variant}`}</UIText>
            <UIText variant="caption">{t('music.compare.seconds', { n: row.track.duration.toFixed(1) })}</UIText>
            {row.track.warning ? (
              <UIText variant="caption">{t('warning.music_short', { n: row.track.duration.toFixed(1) })}</UIText>
            ) : null}
            <UIText variant="caption">{voiceText(row.track.voice)}</UIText>
            <UIText variant="caption">{t('music.compare.lufsValue', { n: row.track.lufs.toFixed(1) })}</UIText>
            <UIText variant="caption">{t('music.style.meta', { key: row.track.key ?? '', bpm: row.track.bpm ?? '' })}</UIText>
            <UIButton
              variant={row.chosen ? 'primary' : 'secondary'}
              aria-pressed={row.chosen}
              onClick={() => choose.mutate(row)}
            >
              {t('music.compare.choose')}
            </UIButton>
          </UIStack>
          <TrackPlayer path={`${row.job.output_dir ?? ''}/${row.track.file}`} />
        </UIStack>
      ))}
      <UIButton variant="secondary" disabled>
        {t('music.compare.mix')}
      </UIButton>
    </UIStack>
  );
}

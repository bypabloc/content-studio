import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useApi } from '@/shared/api/context';
import { UIGrid } from '@/shared/components/atoms/UIGrid';
import { UIIcon } from '@/shared/components/atoms/UIIcon';
import { UIStack } from '@/shared/components/atoms/UIStack';
import { UIText } from '@/shared/components/atoms/UIText';
import { UIIconButton } from '@/shared/components/molecules/UIIconButton';
import { t } from '@/shared/i18n/t';
import { Player } from '@/shared/media/Player';
import { type Job, type Take, useTake } from './useTake';

/** La evaluación de una toma en una palabra: OK, REVISAR, o sin evaluar. */
function verdict(evaluation: Take['evaluation'] | undefined): string {
  if (!evaluation) return t('narration.compare.unevaluated');
  return evaluation.ok ? t('narration.compare.ok') : t('narration.compare.review');
}

/**
 * Las tomas de un mismo texto, en columnas: motor, voz, estilo, semilla, duración, volumen y evaluación, con su
 * reproductor. Al reproducir una, las demás se pausan (AC-10). «Elegir» marca la toma con ★ y quita la de antes (D-4).
 */
export function CompareTakes({ groupKey }: { groupKey: string }) {
  const api = useApi();
  const queryClient = useQueryClient();
  const takes = useQuery({
    queryKey: ['jobs', 'group', groupKey],
    queryFn: () => api.get<Job[]>(`/jobs?group_key=${encodeURIComponent(groupKey)}`),
  });
  const choose = useMutation({
    mutationFn: (id: number) => api.post(`/jobs/${id}/star`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['jobs'] }),
  });
  const done = (takes.data ?? []).filter((job) => job.status === 'done');

  return (
    <UIStack role="region" aria-label={t('narration.compare.title')} gap="sm">
      <UIText variant="heading">{t('narration.compare.title')}</UIText>
      <UIGrid columns={3}>
        {done.map((job) => (
          <TakeColumn key={job.id} job={job} onChoose={() => choose.mutate(job.id)} />
        ))}
      </UIGrid>
    </UIStack>
  );
}

function TakeColumn({ job, onChoose }: { job: Job; onChoose: () => void }) {
  const api = useApi();
  const { wav, take, info, peaks } = useTake(job);
  const params = job.params as { model?: string; voice?: string; style?: string };
  const evaluation = take.data?.evaluation;
  const fields: [string, string][] = [
    [t('narration.compare.field.voice'), params.voice ?? ''],
    [t('narration.compare.field.style'), params.style ?? ''],
    [t('narration.compare.field.seed'), String(take.data?.seed ?? '')],
    [t('narration.compare.field.duration'), info.data ? t('narration.compare.seconds', { n: info.data.duration.toFixed(1) }) : ''],
    [t('narration.compare.field.loudness'), info.data ? `${info.data.lufs.toFixed(1)} LUFS` : ''],
    [t('narration.compare.field.evaluation'), verdict(evaluation)],
  ];

  return (
    <UIStack role="article" gap="sm" className="rounded-md border border-border p-3 text-sm">
      <UIStack direction="row" align="center" justify="between" gap="sm">
        <UIText variant="body" className="font-medium">
          {params.model ?? ''}
        </UIText>
        {job.starred ? (
          <UIStack direction="row" align="center" gap="xs">
            <UIIcon name="star" className="size-4 fill-current" />
            <UIText variant="caption" className="font-medium">
              {t('narration.compare.chosen')}
            </UIText>
          </UIStack>
        ) : (
          <UIIconButton variant="secondary" icon="star" label={t('action.choose')} onClick={onChoose} />
        )}
      </UIStack>
      <UIStack gap="xs">
        {fields.map(([term, value]) => (
          <UIStack key={term} direction="row" justify="between" gap="sm">
            <UIText variant="caption" className="text-xs">
              {term}
            </UIText>
            <UIText variant="body" className="text-xs">
              {value}
            </UIText>
          </UIStack>
        ))}
      </UIStack>
      {peaks.data && <Player src={api.fileUrl(wav)} peaks={peaks.data.peaks} />}
    </UIStack>
  );
}

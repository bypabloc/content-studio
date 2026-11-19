import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useApi } from '@/shared/api/context';
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
    <section aria-label={t('narration.compare.title')} className="flex flex-col gap-3">
      <h3 className="text-sm font-medium">{t('narration.compare.title')}</h3>
      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
        {done.map((job) => (
          <TakeColumn key={job.id} job={job} onChoose={() => choose.mutate(job.id)} />
        ))}
      </div>
    </section>
  );
}

function TakeColumn({ job, onChoose }: { job: Job; onChoose: () => void }) {
  const api = useApi();
  const { wav, take, info, peaks } = useTake(job);
  const params = job.params as { model?: string; voice?: string; style?: string };
  const evaluation = take.data?.evaluation;

  return (
    <article className="flex flex-col gap-2 rounded-md border border-border p-3 text-sm">
      <header className="flex items-center justify-between gap-2">
        <h4 className="font-medium">{params.model}</h4>
        {job.starred ? (
          <span className="flex items-center gap-1 text-xs font-medium">
            <span aria-hidden="true">{'★'}</span>
            <span>{t('narration.compare.chosen')}</span>
          </span>
        ) : (
          <button
            type="button"
            onClick={onChoose}
            className="rounded-md border border-border px-2 py-1 text-xs hover:bg-accent"
          >
            {t('narration.compare.choose')}
          </button>
        )}
      </header>
      <dl className="grid grid-cols-2 gap-x-3 gap-y-1 text-xs">
        <dt className="text-muted-foreground">{t('narration.compare.field.voice')}</dt>
        <dd>{params.voice ?? ''}</dd>
        <dt className="text-muted-foreground">{t('narration.compare.field.style')}</dt>
        <dd>{params.style}</dd>
        <dt className="text-muted-foreground">{t('narration.compare.field.seed')}</dt>
        <dd>{take.data?.seed}</dd>
        <dt className="text-muted-foreground">{t('narration.compare.field.duration')}</dt>
        <dd>{info.data ? t('narration.compare.seconds', { n: info.data.duration.toFixed(1) }) : ''}</dd>
        <dt className="text-muted-foreground">{t('narration.compare.field.loudness')}</dt>
        <dd>{info.data ? `${info.data.lufs.toFixed(1)} LUFS` : ''}</dd>
        <dt className="text-muted-foreground">{t('narration.compare.field.evaluation')}</dt>
        <dd>{verdict(evaluation)}</dd>
      </dl>
      {peaks.data && <Player src={api.fileUrl(wav)} peaks={peaks.data.peaks} />}
    </article>
  );
}

import { useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import type { Job } from '@/shared/api/events';
import { t } from '@/shared/i18n/t';

interface Props {
  job: Job;
  onCancel: (id: number) => void;
  onRetry: (id: number) => void;
}

/** Una fila de la cola: la etapa y el progreso si corre, los botones de cancelar o reintentar, y el asa si está en espera. */
export function JobRow({ job, onCancel, onRetry }: Props) {
  const { attributes, listeners, setActivatorNodeRef, setNodeRef, transform, transition } = useSortable({
    id: job.id,
    disabled: job.status !== 'queued',
  });
  const style = { transform: CSS.Transform.toString(transform), transition };

  return (
    <li
      ref={setNodeRef}
      data-job={job.id}
      style={style}
      className="flex flex-col gap-1 rounded-md border border-border bg-card p-2 text-sm"
    >
      <div className="flex items-center justify-between gap-2">
        <span className="truncate">{kindLabel(job.kind)}</span>
        <span className="text-xs text-muted-foreground">{statusLabel(job.status)}</span>
      </div>
      {job.status === 'running' ? (
        <>
          <progress className="w-full" value={job.progress} max={1} />
          <div className="flex justify-between text-xs text-muted-foreground">
            <span>{t('queue.progress', { percent: Math.round(job.progress * 100) })}</span>
            <span>{job.stage}</span>
          </div>
        </>
      ) : null}
      <div className="flex items-center gap-1">
        {job.status === 'queued' ? (
          <button
            type="button"
            ref={setActivatorNodeRef}
            aria-label={t('queue.drag')}
            className="cursor-grab rounded px-1 text-muted-foreground"
            {...attributes}
            aria-roledescription={t('queue.drag_role')}
            {...listeners}
          >
            {'⋮⋮'}
          </button>
        ) : null}
        {job.status === 'queued' || job.status === 'running' ? (
          <button type="button" onClick={() => onCancel(job.id)} className="ml-auto text-xs underline">
            {t('queue.cancel')}
          </button>
        ) : null}
        {job.status === 'error' || job.status === 'cancelled' ? (
          <button type="button" onClick={() => onRetry(job.id)} className="ml-auto text-xs underline">
            {t('queue.retry')}
          </button>
        ) : null}
      </div>
    </li>
  );
}

function kindLabel(kind: string): string {
  if (kind === 'music') return t('queue.kind.music');
  if (kind === 'narration') return t('queue.kind.narration');
  return kind;
}

function statusLabel(status: Job['status']): string {
  switch (status) {
    case 'queued':
      return t('queue.status.queued');
    case 'running':
      return t('queue.status.running');
    case 'error':
      return t('queue.status.error');
    default:
      return t('queue.status.cancelled');
  }
}

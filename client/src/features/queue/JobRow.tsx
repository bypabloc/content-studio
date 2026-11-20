import { useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { UIButton } from '@/shared/components/atoms/UIButton';
import { UIProgress } from '@/shared/components/atoms/UIProgress';
import { UIStack } from '@/shared/components/atoms/UIStack';
import { UIText } from '@/shared/components/atoms/UIText';
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
  const progress = t('queue.progress', { percent: Math.round(job.progress * 100) });

  return (
    <UIStack
      ref={setNodeRef}
      role="listitem"
      data-job={job.id}
      style={style}
      gap="sm"
      className="rounded-md border border-border bg-card p-2 text-sm"
    >
      <UIStack direction="row" justify="between" gap="sm">
        <UIText variant="body" className="truncate">
          {kindLabel(job.kind)}
        </UIText>
        <UIText variant="caption">{statusLabel(job.status)}</UIText>
      </UIStack>
      {job.status === 'running' ? (
        <UIStack gap="sm">
          <UIProgress value={job.progress} label={progress} />
          <UIStack direction="row" justify="between" gap="sm">
            <UIText variant="caption">{progress}</UIText>
            <UIText variant="caption">{job.stage}</UIText>
          </UIStack>
        </UIStack>
      ) : null}
      <UIStack direction="row" align="center" gap="sm">
        {job.status === 'queued' ? (
          <UIButton
            ref={setActivatorNodeRef}
            variant="ghost"
            aria-label={t('queue.drag')}
            {...attributes}
            aria-roledescription={t('queue.drag_role')}
            {...listeners}
          >
            {'⋮⋮'}
          </UIButton>
        ) : null}
        {job.status === 'queued' || job.status === 'running' ? (
          <UIButton variant="ghost" className="ml-auto" onClick={() => onCancel(job.id)}>
            {t('queue.cancel')}
          </UIButton>
        ) : null}
        {job.status === 'error' || job.status === 'cancelled' ? (
          <UIButton variant="ghost" className="ml-auto" onClick={() => onRetry(job.id)}>
            {t('queue.retry')}
          </UIButton>
        ) : null}
      </UIStack>
    </UIStack>
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

import { lazy, Suspense } from 'react';
import { useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { UIIcon, type IconName } from '@/shared/components/atoms/UIIcon';
import { UIProgress } from '@/shared/components/atoms/UIProgress';
import { UIStack } from '@/shared/components/atoms/UIStack';
import { UIText } from '@/shared/components/atoms/UIText';
import { UIIconButton } from '@/shared/components/molecules/UIIconButton';
import type { Job } from '@/shared/api/events';
import { t } from '@/shared/i18n/t';

const OpenJobOutputButton = lazy(() =>
  import('@/shared/navigation/OpenJobOutputButton').then((module) => ({ default: module.OpenJobOutputButton })),
);

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
        <UIStack direction="row" align="center" gap="xs">
          <UIIcon name={statusIcon(job.status)} className={job.status === 'running' ? 'size-4 animate-spin motion-reduce:animate-none' : 'size-4'} />
          <UIText variant="caption">{statusLabel(job.status)}</UIText>
        </UIStack>
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
        {job.status === 'done' && job.output_dir ? (
          <Suspense fallback={null}>
            <OpenJobOutputButton outputDir={job.output_dir} />
          </Suspense>
        ) : null}
        {job.status === 'queued' ? (
          <UIIconButton
            ref={setActivatorNodeRef}
            icon="drag-handle"
            label={t('action.drag')}
            {...attributes}
            aria-roledescription={t('queue.drag_role')}
            {...listeners}
          />
        ) : null}
        {job.status === 'queued' || job.status === 'running' ? (
          <UIIconButton icon="cancel" label={t('action.cancel')} className="ml-auto size-11 px-0" onClick={() => onCancel(job.id)} />
        ) : null}
        {job.status === 'error' || job.status === 'cancelled' ? (
          <UIIconButton icon="retry" label={t('action.retry')} className="ml-auto size-11 px-0" onClick={() => onRetry(job.id)} />
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
    case 'done':
      return t('queue.status.done');
    case 'error':
      return t('queue.status.error');
    default:
      return t('queue.status.cancelled');
  }
}

/** Ícono del estado: en cola, corriendo (con giro), listo, error o cancelado (spec 009, D-5). */
function statusIcon(status: Job['status']): IconName {
  switch (status) {
    case 'queued':
      return 'clock';
    case 'running':
      return 'loader-circle';
    case 'error':
      return 'circle-alert';
    case 'done':
      return 'circle-check';
    default:
      return 'ban';
  }
}

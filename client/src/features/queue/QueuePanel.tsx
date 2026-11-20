import { DndContext, KeyboardSensor, PointerSensor, closestCenter, useSensor, useSensors, type DragEndEvent } from '@dnd-kit/core';
import { SortableContext, sortableKeyboardCoordinates, verticalListSortingStrategy } from '@dnd-kit/sortable';
import { useState } from 'react';
import { UIStack } from '@/shared/components/atoms/UIStack';
import { UIText } from '@/shared/components/atoms/UIText';
import { UIIconButton } from '@/shared/components/molecules/UIIconButton';
import { t } from '@/shared/i18n/t';
import { reorderAccessibility } from './announce';
import { JobRow } from './JobRow';
import { dropOrder } from './order';
import { useQueue } from './useQueue';

/** La cola en la sidebar: pausar, reordenar arrastrando los que esperan, cancelar, reintentar; su botón oculta la lista (D-6). */
export function QueuePanel() {
  const queue = useQueue();
  const [open, setOpen] = useState(true);
  const visible = queue.jobs.filter((job) => job.status !== 'done');
  const waiting = visible.filter((job) => job.status === 'queued').map((job) => job.id);
  // El teclado pasa a la fila vecina; con las coordenadas por defecto (25 px) el `over` no cambia y no reordena.
  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates }),
  );

  const onDragEnd = (event: DragEndEvent) => {
    const ids = dropOrder(queue.jobs, Number(event.active.id), event.over ? Number(event.over.id) : null);
    if (ids) queue.reorder(ids);
  };

  return (
    <UIStack role="region" aria-label={t('queue.title')} gap="sm">
      <UIStack direction="row" align="center" justify="between" gap="sm" className="flex-wrap">
        <UIText variant="subtitle" className="text-sm">
          {t('queue.title')}
        </UIText>
        <UIStack direction="row" gap="sm" className="flex-wrap">
          <UIIconButton
            icon={queue.paused ? 'play' : 'pause'}
            label={queue.paused ? t('action.resume') : t('action.pause')}
            onClick={queue.togglePause}
          />
          <UIIconButton
            icon={open ? 'chevron-down' : 'chevron-up'}
            label={open ? t('action.collapse') : t('action.expand')}
            aria-expanded={open}
            onClick={() => setOpen(!open)}
          />
        </UIStack>
      </UIStack>
      {open ? (
        <>
          {visible.length === 0 ? <UIText variant="caption">{t('queue.empty')}</UIText> : null}
          <DndContext
            sensors={sensors}
            collisionDetection={closestCenter}
            onDragEnd={onDragEnd}
            accessibility={reorderAccessibility(waiting)}
          >
            <SortableContext items={waiting} strategy={verticalListSortingStrategy}>
              <UIStack role="list" gap="sm">
                {visible.map((job) => (
                  <JobRow key={job.id} job={job} onCancel={queue.cancel} onRetry={queue.retry} />
                ))}
              </UIStack>
            </SortableContext>
          </DndContext>
        </>
      ) : null}
    </UIStack>
  );
}

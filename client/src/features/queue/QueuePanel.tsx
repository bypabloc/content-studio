import { DndContext, KeyboardSensor, PointerSensor, closestCenter, useSensor, useSensors, type DragEndEvent } from '@dnd-kit/core';
import { SortableContext, sortableKeyboardCoordinates, verticalListSortingStrategy } from '@dnd-kit/sortable';
import { useState } from 'react';
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
    <section aria-label={t('queue.title')} className="flex flex-col gap-2">
      <div className="flex items-center justify-between gap-2">
        <h2 className="text-xs font-medium uppercase text-muted-foreground">{t('queue.title')}</h2>
        <div className="flex gap-2">
          <button type="button" onClick={queue.togglePause} className="text-xs underline">
            {queue.paused ? t('queue.resume') : t('queue.pause')}
          </button>
          <button type="button" aria-expanded={open} onClick={() => setOpen(!open)} className="text-xs underline">
            {open ? t('queue.collapse') : t('queue.expand')}
          </button>
        </div>
      </div>
      {open ? (
        <>
          {visible.length === 0 ? <p className="text-xs text-muted-foreground">{t('queue.empty')}</p> : null}
          <DndContext
            sensors={sensors}
            collisionDetection={closestCenter}
            onDragEnd={onDragEnd}
            accessibility={reorderAccessibility(waiting)}
          >
            <SortableContext items={waiting} strategy={verticalListSortingStrategy}>
              <ul className="flex flex-col gap-1">
                {visible.map((job) => (
                  <JobRow key={job.id} job={job} onCancel={queue.cancel} onRetry={queue.retry} />
                ))}
              </ul>
            </SortableContext>
          </DndContext>
        </>
      ) : null}
    </section>
  );
}

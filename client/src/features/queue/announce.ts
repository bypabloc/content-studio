import type { UniqueIdentifier } from '@dnd-kit/core';
import { t } from '@/shared/i18n/t';

/**
 * Lo que dnd-kit anuncia al lector de pantalla al reordenar la cola con el teclado. El lugar de cada trabajo sale de
 * `waiting` (los ids en espera, en orden): «posición 1 de 2». Sin destino, no se anuncia lugar.
 */
export function reorderAccessibility(waiting: readonly number[]) {
  const place = (id: UniqueIdentifier) => ({ position: waiting.indexOf(Number(id)) + 1, total: waiting.length });
  return {
    screenReaderInstructions: { draggable: t('queue.reorder_help') },
    announcements: {
      onDragStart: () => t('queue.announce.picked'),
      onDragOver: ({ over }: { over: { id: UniqueIdentifier } | null }) =>
        over ? t('queue.announce.moved', place(over.id)) : undefined,
      onDragEnd: ({ over }: { over: { id: UniqueIdentifier } | null }) =>
        over ? t('queue.announce.dropped', place(over.id)) : undefined,
      onDragCancel: () => t('queue.announce.cancelled'),
    },
  };
}

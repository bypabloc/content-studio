import { useRef } from 'react';
import type { PointerEvent as ReactPointerEvent } from 'react';

import { UIButton } from '@/shared/components/atoms/UIButton';
import { UIStack } from '@/shared/components/atoms/UIStack';
import { t } from '@/shared/i18n/t';

import type { Transition } from './model/types';

type Props = {
  transition: Transition;
  left: number;
  zoom: number;
  locked: boolean;
  onResize: (id: string, duration: number) => void;
  onCommitResize: () => void;
  onCancelResize?: () => void;
};
type Edge = 'start' | 'end';
type Drag = { edge: Edge; origin: number; duration: number; moved: boolean };

/** Zona de transición entre clips; ambos bordes ajustan el solapamiento de entrada. */
export function TransitionZone({
  transition, left, zoom, locked, onResize, onCommitResize, onCancelResize = () => undefined,
}: Props): React.JSX.Element {
  const dragRef = useRef<Drag | null>(null);

  function begin(edge: Edge, event: ReactPointerEvent<HTMLButtonElement>): void {
    if (locked) return;
    event.preventDefault();
    event.stopPropagation();
    dragRef.current = { edge, origin: event.clientX, duration: transition.duration, moved: false };
    event.currentTarget.setPointerCapture?.(event.pointerId);
  }

  function update(event: ReactPointerEvent<HTMLButtonElement>): void {
    const drag = dragRef.current;
    if (!drag) return;
    const direction = drag.edge === 'start' ? -1 : 1;
    const duration = Math.max(1 / 120, drag.duration + direction * ((event.clientX - drag.origin) / zoom));
    drag.moved = true;
    onResize(transition.id, duration);
  }

  function finish(event: ReactPointerEvent<HTMLButtonElement>): void {
    update(event);
    const drag = dragRef.current;
    dragRef.current = null;
    if (drag?.moved) onCommitResize();
  }

  return (
    <UIStack
      role="group"
      aria-label={t('editor.transition.zone', { type: transition.type })}
      direction="row"
      align="center"
      justify="between"
      className="absolute top-1 z-30 h-8 overflow-hidden rounded-md border border-primary bg-primary/30"
      style={{ left: `${left}px`, width: `${transition.duration * zoom}px` }}
    >
      <UIButton
        aria-label={t('editor.transition.resize_start')}
        disabled={locked}
        className="h-full min-h-0 w-3 min-w-3 rounded-none p-0"
        onPointerDown={(event) => begin('start', event)}
        onPointerMove={update}
        onPointerUp={finish}
        onPointerCancel={() => {
          if (dragRef.current?.moved) onCancelResize();
          dragRef.current = null;
        }}
      />
      <UIButton
        aria-label={t('editor.transition.resize_end')}
        disabled={locked}
        className="h-full min-h-0 w-3 min-w-3 rounded-none p-0"
        onPointerDown={(event) => begin('end', event)}
        onPointerMove={update}
        onPointerUp={finish}
        onPointerCancel={() => {
          if (dragRef.current?.moved) onCancelResize();
          dragRef.current = null;
        }}
      />
    </UIStack>
  );
}

import type { DragEvent } from 'react';

import { UIButton } from '@/shared/components/atoms/UIButton';
import { UIStack } from '@/shared/components/atoms/UIStack';
import { UIText } from '@/shared/components/atoms/UIText';
import { t } from '@/shared/i18n/t';

import type { TransitionType } from './model/types';

const MIME = 'application/x-editor-transition';
// cspell:ignore fadeblack fadewhite wipeleft wiperight slideleft slideright circleopen: identificadores xfade de FFmpeg.
const TRANSITIONS: Array<{ type: TransitionType; label: string }> = [
  { type: 'fade', label: t('editor.transitions.fade') },
  { type: 'fadeblack', label: t('editor.transitions.fade_black') },
  { type: 'fadewhite', label: t('editor.transitions.fade_white') },
  { type: 'wipeleft', label: t('editor.transitions.wipe_left') },
  { type: 'wiperight', label: t('editor.transitions.wipe_right') },
  { type: 'slideleft', label: t('editor.transitions.slide_left') },
  { type: 'slideright', label: t('editor.transitions.slide_right') },
  { type: 'circleopen', label: t('editor.transitions.circle_open') },
];

type Props = { onAdd: (type: TransitionType) => void };

function startDrag(type: TransitionType, event: DragEvent<HTMLButtonElement>): void {
  event.dataTransfer.setData(MIME, type);
  event.dataTransfer.effectAllowed = 'copy';
}

/** Tipos de transición disponibles por clic o arrastre a un corte de video. */
export function TransitionsPanel({ onAdd }: Props): React.JSX.Element {
  return (
    <UIStack role="group" aria-label={t('editor.transitions.label')} gap="xs">
      <UIText variant="heading">{t('editor.transitions.label')}</UIText>
      {TRANSITIONS.map(({ type, label }) => (
          <UIButton
            key={type}
            variant="secondary"
            draggable
            onClick={() => onAdd(type)}
            onDragStart={(event) => startDrag(type, event)}
          >
            {label}
          </UIButton>
      ))}
    </UIStack>
  );
}

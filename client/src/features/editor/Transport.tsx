import type { KeyboardEvent } from 'react';

import { UIStack } from '@/shared/components/atoms/UIStack';
import { UIIconButton } from '@/shared/components/molecules/UIIconButton';
import { t } from '@/shared/i18n/t';

import { ZOOM_LEVELS, zoomIn, zoomOut } from './model/timeline';

const SHORTCUTS = {
  all: 'Home Space R N + -', // i18n-ignore: secuencia estándar de teclas de acceso rápido
  home: 'Home', // i18n-ignore: nombre estándar de tecla
  space: 'Space', // i18n-ignore: nombre estándar de tecla
  record: 'R', // i18n-ignore: tecla de acceso rápido
  magnet: 'N', // i18n-ignore: tecla de acceso rápido
} as const;

type Props = {
  playing: boolean;
  recording: boolean;
  magnet: boolean;
  zoom: number;
  onStart: () => void;
  onPlayingChange: (playing: boolean) => void;
  onStop: () => void;
  onRecordingChange: (recording: boolean) => void;
  onMagnetChange: (magnet: boolean) => void;
  onZoomChange: (zoom: number) => void;
};

/** Controles de reproducción y atajos del transporte de la línea de tiempo. */
export function Transport({
  playing,
  recording,
  magnet,
  zoom,
  onStart,
  onPlayingChange,
  onStop,
  onRecordingChange,
  onMagnetChange,
  onZoomChange,
}: Props): React.JSX.Element {
  function changeZoom(direction: -1 | 1): void {
    onZoomChange(direction === 1 ? zoomIn(zoom) : zoomOut(zoom));
  }

  function onKeyDown(event: KeyboardEvent<HTMLDivElement>): void {
    if (event.repeat) return;
    const key = event.key.toLowerCase();
    if (event.key === 'Home') onStart();
    else if (event.key === ' ' || event.key === 'Spacebar') onPlayingChange(!playing);
    else if (key === 'r') onRecordingChange(!recording);
    else if (key === 'n') onMagnetChange(!magnet);
    else if (event.key === '+' || event.key === '=') changeZoom(1);
    else if (event.key === '-' || event.key === '_') changeZoom(-1);
    else return;
    event.preventDefault();
  }

  return (
    <UIStack
      role="toolbar"
      aria-label={t('editor.transport.label')}
      aria-keyshortcuts={SHORTCUTS.all}
      className="border-b border-border bg-card px-3 py-2"
      direction="row"
      align="center"
      gap="xs"
      tabIndex={0}
      onKeyDown={onKeyDown}
    >
      <UIIconButton icon="chevron-left" label={t('editor.transport.start')} shortcut={SHORTCUTS.home} onClick={onStart} />
      <UIIconButton
        icon={playing ? 'pause' : 'play'}
        label={playing ? t('editor.transport.pause') : t('editor.transport.play')}
        shortcut={SHORTCUTS.space}
        onClick={() => onPlayingChange(!playing)}
      />
      <UIIconButton
        icon="stop"
        label={t('editor.transport.stop')}
        onClick={() => {
          onStop();
          onPlayingChange(false);
          if (recording) onRecordingChange(false);
        }}
      />
      <UIIconButton
        icon="record"
        label={t('editor.transport.record')}
        shortcut={SHORTCUTS.record}
        pressed={recording}
        onClick={() => onRecordingChange(!recording)}
      />
      <UIIconButton
        icon="magnet"
        label={t('editor.transport.magnet')}
        shortcut={SHORTCUTS.magnet}
        pressed={magnet}
        onClick={() => onMagnetChange(!magnet)}
      />
      <UIIconButton
        icon="minus"
        label={t('editor.transport.zoom_out')}
        shortcut="-"
        disabled={zoom <= ZOOM_LEVELS[0]}
        onClick={() => changeZoom(-1)}
      />
      <UIIconButton
        icon="plus"
        label={t('editor.transport.zoom_in')}
        shortcut="+"
        disabled={zoom >= ZOOM_LEVELS[ZOOM_LEVELS.length - 1]}
        onClick={() => changeZoom(1)}
      />
    </UIStack>
  );
}

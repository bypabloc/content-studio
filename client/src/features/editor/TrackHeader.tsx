import type { KeyboardEvent } from 'react';

import { UILevelMeter } from '@/shared/components/atoms/UILevelMeter';
import { UIRangeInput } from '@/shared/components/atoms/UIRangeInput';
import { UIStack } from '@/shared/components/atoms/UIStack';
import { UIText } from '@/shared/components/atoms/UIText';
import { UIIconButton } from '@/shared/components/molecules/UIIconButton';
import { t } from '@/shared/i18n/t';

import type { Op, Track } from './model/types';
import type { Levels } from '@/features/recording/capture/useRecorder';

type Props = {
  track: Track;
  armed: boolean;
  levels?: Levels;
  onChange: (op: Op) => void;
  onArmedChange: (armed: boolean) => void;
};

const MUTE_SHORTCUT = 'M'; // i18n-ignore: tecla de acceso rápido estándar

/** Controles persistidos y de grabación temporal de una pista de audio. */
export function TrackHeader({ track, armed, levels, onChange, onArmedChange }: Props): React.JSX.Element {
  function onKeyDown(event: KeyboardEvent<HTMLDivElement>): void {
    if (track.kind !== 'audio' || event.key.toLowerCase() !== 'm' || event.repeat) return;
    event.preventDefault();
    onChange({ type: 'setTrack', id: track.id, changes: { mute: !track.mute } });
  }

  return (
    <UIStack
      role="group"
      aria-label={track.name}
      aria-keyshortcuts={track.kind === 'audio' ? MUTE_SHORTCUT : undefined}
      className="min-w-56 border-r border-border bg-card px-3 py-2"
      direction="column"
      gap="xs"
      tabIndex={0}
      onKeyDown={onKeyDown}
    >
      <UIStack direction="row" align="center" justify="between" gap="sm">
        <UIText variant="heading" className="truncate">{track.name}</UIText>
        <UIStack direction="row" align="center" gap="xs">
          {track.kind === 'audio' ? (
            <>
              <UIIconButton
                icon={track.mute ? 'mute' : 'volume'}
                label={t('editor.track.mute', { name: track.name })}
                pressed={track.mute}
                shortcut={MUTE_SHORTCUT}
                aria-keyshortcuts={MUTE_SHORTCUT}
                onClick={() => onChange({ type: 'setTrack', id: track.id, changes: { mute: !track.mute } })}
              />
              <UIIconButton
                icon="music"
                label={t('editor.track.solo', { name: track.name })}
                pressed={track.solo}
                onClick={() => onChange({ type: 'setTrack', id: track.id, changes: { solo: !track.solo } })}
              />
            </>
          ) : null}
          <UIIconButton
            icon="lock"
            label={t('editor.track.lock', { name: track.name })}
            pressed={track.locked}
            onClick={() => onChange({ type: 'setTrack', id: track.id, changes: { locked: !track.locked } })}
          />
          {track.kind === 'audio' ? (
            <UIIconButton
              icon="record"
              label={t('editor.track.arm', { name: track.name })}
              pressed={armed}
              onClick={() => onArmedChange(!armed)}
            />
          ) : null}
        </UIStack>
      </UIStack>
      {track.kind === 'audio' ? (
        <UIRangeInput
          label={t('editor.track.volume', { name: track.name })}
          min={-60}
          max={12}
          step={0.1}
          value={track.volume_db}
          onValueChange={(volume_db) => onChange({ type: 'setTrack', id: track.id, changes: { volume_db } })}
        />
      ) : null}
      {track.kind === 'audio' && armed && levels ? (
        <UILevelMeter label={t('editor.recorder.level')} rms={levels.rms} peak={levels.peak} zone={[-12, -6]} alertAbove={-1} />
      ) : null}
    </UIStack>
  );
}

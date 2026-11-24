import { UIButton } from '@/shared/components/atoms/UIButton';
import { UILevelMeter } from '@/shared/components/atoms/UILevelMeter';
import { UIStack } from '@/shared/components/atoms/UIStack';
import { UIText } from '@/shared/components/atoms/UIText';
import { t } from '@/shared/i18n/t';
import type { Levels } from './capture/useRecorder';

// La zona verde de la guía (de −12 a −6 dB) y el aviso rojo desde −1 dB (spec 010, D-2).
const ZONE: readonly [number, number] = [-12, -6];
const ALERT_ABOVE = -1;

type Props = {
  recording: boolean;
  levels: Levels;
  elapsed: number;
  target: { min: number; max: number };
  disabled?: boolean;
  onToggle: () => void;
};

/** Grabar o parar, el reloj con el rango objetivo y el medidor del nivel de entrada (spec 010, D-6). */
export function RecordControls({ recording, levels, elapsed, target, disabled = false, onToggle }: Props): React.JSX.Element {
  const inRange = elapsed >= target.min && elapsed <= target.max;
  return (
    <UIStack gap="md">
      <UIStack direction="row" align="center" gap="md">
        <UIButton
          variant={recording ? 'danger' : 'primary'}
          icon={recording ? 'stop' : 'record'}
          disabled={disabled}
          onClick={onToggle}
        >
          {recording ? t('voices.record.stop') : t('voices.record.start')}
        </UIButton>
        <UIText variant="subtitle">{elapsed.toFixed(1)}</UIText>
        {recording ? (
          <UIText variant="caption">{inRange ? t('voices.record.in_range') : t('voices.record.out_of_range')}</UIText>
        ) : null}
      </UIStack>
      <UILevelMeter label={t('voices.record.level')} rms={levels.rms} peak={levels.peak} zone={ZONE} alertAbove={ALERT_ABOVE} />
    </UIStack>
  );
}

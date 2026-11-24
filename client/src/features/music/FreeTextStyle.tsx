import { UIButton } from '@/shared/components/atoms/UIButton';
import { UIStack } from '@/shared/components/atoms/UIStack';
import { UIText } from '@/shared/components/atoms/UIText';
import { UIField } from '@/shared/components/molecules/UIField';
import { t } from '@/shared/i18n/t';

import { useTapTempo } from './useTapTempo';

/** Lo que se escribe en «Texto libre»: la descripción en inglés, la tonalidad, el BPM y el compás (spec 011, D-5). */
export interface FreeText {
  caption: string;
  key: string | null;
  bpm: number | null;
  timeSignature: string | null;
}

const TIME_SIGNATURES = [
  { value: '2', label: '2/4' },
  { value: '3', label: '3/4' },
  { value: '4', label: '4/4' },
  { value: '6', label: '6/8' },
];
const MIN_BPM = 30;
const MAX_BPM = 300;

/** Generar solo se habilita con descripción, tonalidad y BPM (30–300) elegidos. El compás siempre tiene valor. */
export function freeTextComplete(value: FreeText): boolean {
  return (
    value.caption.trim() !== '' &&
    value.key !== null &&
    value.bpm !== null &&
    value.bpm >= MIN_BPM &&
    value.bpm <= MAX_BPM &&
    value.timeSignature !== null
  );
}

interface FreeTextStyleProps {
  value: FreeText;
  /** Tonalidades estables del catálogo, en el orden en que se muestran. */
  keys: string[];
  onChange: (next: FreeText) => void;
}

/** Formulario del modo «Texto libre»: descripción, tonalidad, BPM (campo o tap tempo) y compás. */
export function FreeTextStyle({ value, keys, onChange }: FreeTextStyleProps): React.JSX.Element {
  const tempo = useTapTempo();
  return (
    <UIStack gap="md">
      <UIText variant="caption">{t('music.freeText.hint')}</UIText>
      <UIField
        label={t('music.freeText.caption')}
        value={value.caption}
        onChange={(event) => onChange({ ...value, caption: event.target.value })}
      />
      <UIStack gap="sm">
        <UIText variant="caption">{t('music.freeText.key')}</UIText>
        <UIStack direction="row" gap="sm" className="flex-wrap">
          {keys.map((key) => (
            <UIButton
              key={key}
              variant={value.key === key ? 'primary' : 'secondary'}
              aria-pressed={value.key === key}
              onClick={() => onChange({ ...value, key })}
            >
              {key}
            </UIButton>
          ))}
        </UIStack>
      </UIStack>
      <UIField
        label={t('music.freeText.bpm')}
        type="number"
        min={MIN_BPM}
        max={MAX_BPM}
        value={value.bpm ?? ''}
        onChange={(event) => {
          const bpm = Number(event.target.value);
          onChange({ ...value, bpm: event.target.value === '' || !Number.isInteger(bpm) ? null : bpm });
        }}
      />
      <UIButton
        variant="secondary"
        onClick={() => {
          const bpm = tempo.tap(Date.now());
          if (bpm !== null) onChange({ ...value, bpm });
        }}
      >
        {t('music.freeText.tap')}
      </UIButton>
      <UIStack gap="sm">
        <UIText variant="caption">{t('music.freeText.timeSignature')}</UIText>
        <UIStack direction="row" gap="sm">
          {TIME_SIGNATURES.map((signature) => (
            <UIButton
              key={signature.value}
              variant={value.timeSignature === signature.value ? 'primary' : 'secondary'}
              aria-pressed={value.timeSignature === signature.value}
              onClick={() => onChange({ ...value, timeSignature: signature.value })}
            >
              {signature.label}
            </UIButton>
          ))}
        </UIStack>
      </UIStack>
    </UIStack>
  );
}

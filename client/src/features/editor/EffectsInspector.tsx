import { useState } from 'react';

import { UIButton } from '@/shared/components/atoms/UIButton';
import { UICard } from '@/shared/components/atoms/UICard';
import { UIField } from '@/shared/components/molecules/UIField';
import { UISelect } from '@/shared/components/molecules/UISelect';
import { UIStack } from '@/shared/components/atoms/UIStack';
import { UIText } from '@/shared/components/atoms/UIText';
import { t } from '@/shared/i18n/t';

import type { BlendMode, ChromaKey, VisualClip } from './model/types';

type Change = { blend_mode?: BlendMode; chroma?: ChromaKey | null };
type Props = { clip: VisualClip | null; onChange: (id: string, change: Change) => void };
type EyeDropperResult = { sRGBHex: string };
type EyeDropperConstructor = new () => { open: () => Promise<EyeDropperResult> };

const DEFAULT_CHROMA: ChromaKey = { color: '#00ff00', similarity: 0.2, blend: 0.1 };
const MODES: BlendMode[] = ['normal', 'multiply', 'screen', 'overlay', 'darken', 'lighten', 'add', 'difference'];

/** Ajusta la clave de color, el cuentagotas y el modo de fusión del clip visual. */
export function EffectsInspector({ clip, onChange }: Props): React.JSX.Element | null {
  const [pickerError, setPickerError] = useState(false);
  if (!clip) return null;
  const clipId = clip.id;
  const chroma = clip.chroma ?? DEFAULT_CHROMA;
  const labels: Record<BlendMode, string> = {
    normal: t('editor.effects.blend.normal'),
    multiply: t('editor.effects.blend.multiply'),
    screen: t('editor.effects.blend.screen'),
    overlay: t('editor.effects.blend.overlay'),
    darken: t('editor.effects.blend.darken'),
    lighten: t('editor.effects.blend.lighten'),
    add: t('editor.effects.blend.add'),
    difference: t('editor.effects.blend.difference'),
  };
  const options = MODES.map((mode) => ({ value: mode, label: labels[mode] }));

  function pickColor(): void {
    const EyeDropper = (window as Window & { EyeDropper?: EyeDropperConstructor }).EyeDropper;
    if (!EyeDropper) {
      setPickerError(true);
      return;
    }
    void new EyeDropper().open().then(({ sRGBHex }) => {
      onChange(clipId, { chroma: { ...chroma, color: sRGBHex } });
      setPickerError(false);
    }).catch(() => undefined);
  }

  return (
    <UICard aria-label={t('editor.effects.title')}>
      <UIStack gap="sm">
        <UIText variant="heading">{t('editor.effects.title')}</UIText>
        <UISelect
          label={t('editor.effects.mode')}
          value={clip.blend_mode ?? 'normal'}
          options={options}
          onChange={(value) => onChange(clipId, { blend_mode: value as BlendMode })}
        />
        <UIButton
          variant="secondary"
          aria-pressed={Boolean(clip.chroma)}
          onClick={() => onChange(clipId, { chroma: clip.chroma ? null : DEFAULT_CHROMA })}
        >
          {clip.chroma ? t('editor.effects.chroma.remove') : t('editor.effects.chroma.enable')}
        </UIButton>
        {clip.chroma ? (
          <>
            <UIStack direction="row" align="end" gap="xs">
              <UIField
                label={t('editor.effects.chroma.color')}
                type="color"
                value={chroma.color}
                onChange={(event) => onChange(clipId, { chroma: { ...chroma, color: event.currentTarget.value } })}
              />
              <UIButton variant="secondary" onClick={pickColor}>{t('editor.effects.chroma.pick')}</UIButton>
            </UIStack>
            <UIField
              label={t('editor.effects.chroma.similarity')}
              type="number"
              min={0}
              max={1}
              step={0.01}
              value={chroma.similarity}
              onChange={(event) => {
                const value = Number(event.currentTarget.value);
                if (Number.isFinite(value)) onChange(clipId, { chroma: { ...chroma, similarity: Math.min(1, Math.max(0, value)) } });
              }}
            />
            <UIField
              label={t('editor.effects.chroma.blend')}
              type="number"
              min={0}
              max={1}
              step={0.01}
              value={chroma.blend}
              onChange={(event) => {
                const value = Number(event.currentTarget.value);
                if (Number.isFinite(value)) onChange(clipId, { chroma: { ...chroma, blend: Math.min(1, Math.max(0, value)) } });
              }}
            />
            <UIField
              label={t('editor.effects.chroma.despill')}
              type="checkbox"
              checked={chroma.despill ?? false}
              onChange={(event) => onChange(clipId, { chroma: { ...chroma, despill: event.currentTarget.checked } })}
            />
            {pickerError ? <UIText role="alert" variant="caption">{t('editor.effects.chroma.error')}</UIText> : null}
          </>
        ) : null}
      </UIStack>
    </UICard>
  );
}

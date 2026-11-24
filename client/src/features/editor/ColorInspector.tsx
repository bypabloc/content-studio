import { useState } from 'react';

import { useApi } from '@/shared/api/context';
import { UIButton } from '@/shared/components/atoms/UIButton';
import { UICard } from '@/shared/components/atoms/UICard';
import { UIField } from '@/shared/components/molecules/UIField';
import { UIStack } from '@/shared/components/atoms/UIStack';
import { UIText } from '@/shared/components/atoms/UIText';
import { t } from '@/shared/i18n/t';

import type { ColorEffects, VisualClip } from './model/types';

type Props = {
  clip: VisualClip | null;
  path: string;
  onChange: (id: string, color: ColorEffects) => void;
};

type ColorKey = 'brightness' | 'contrast' | 'saturation' | 'gamma';
type ColorControl = { key: ColorKey; min: number; max: number; step: number };

const DEFAULT_COLOR: ColorEffects = { brightness: 0, contrast: 1, saturation: 1, gamma: 1 };
const CONTROLS: ColorControl[] = [
  { key: 'brightness', min: -1, max: 1, step: 0.01 },
  { key: 'contrast', min: 0, max: 2, step: 0.01 },
  { key: 'saturation', min: 0, max: 3, step: 0.01 },
  { key: 'gamma', min: 0.1, max: 10, step: 0.1 },
];

/** Controles de color y subida de LUT 3D para el clip visual seleccionado. */
export function ColorInspector({ clip, path, onChange }: Props): React.JSX.Element | null {
  const api = useApi();
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState(false);
  if (!clip) return null;
  const clipId = clip.id;
  const color = clip.color ?? DEFAULT_COLOR;
  const labels: Record<ColorKey, string> = {
    brightness: t('editor.color.brightness'),
    contrast: t('editor.color.contrast'),
    saturation: t('editor.color.saturation'),
    gamma: t('editor.color.gamma'),
  };

  async function uploadLut(event: React.ChangeEvent<HTMLInputElement>): Promise<void> {
    const input = event.currentTarget;
    const file = input.files?.[0];
    if (!file) return;
    setUploading(true);
    setError(false);
    try {
      const query = new URLSearchParams({ path });
      const uploaded = await api.upload<{ src: string }>(`/editor/projects/luts?${query}`, file, 'text/plain');
      onChange(clipId, { ...color, lut: uploaded.src });
    } catch {
      setError(true);
    } finally {
      setUploading(false);
      input.value = '';
    }
  }

  return (
    <UICard aria-label={t('editor.color.title')}>
      <UIStack gap="sm">
        <UIText variant="heading">{t('editor.color.title')}</UIText>
        {CONTROLS.map(({ key, min, max, step }) => (
          <UIField
            key={key}
            label={labels[key]}
            type="number"
            min={min}
            max={max}
            step={step}
            value={color[key]}
            onChange={(event) => {
              const value = Number(event.currentTarget.value);
              if (Number.isFinite(value)) onChange(clipId, { ...color, [key]: Math.min(max, Math.max(min, value)) });
            }}
          />
        ))}
        <UIField
          type="file"
          label={t('editor.color.lut')}
          accept=".cube,text/plain"
          hint={t('editor.color.lut_hint')}
          disabled={uploading}
          onChange={(event) => void uploadLut(event)}
        />
        {color.lut ? (
          <UIButton variant="secondary" onClick={() => {
            const { lut: _lut, ...withoutLut } = color;
            onChange(clipId, withoutLut);
          }}>{t('editor.color.lut_remove')}</UIButton>
        ) : null}
        {error ? <UIText role="alert" variant="caption">{t('editor.color.lut_error')}</UIText> : null}
      </UIStack>
    </UICard>
  );
}

import { useEffect, useRef, useState } from 'react';

import { UIField } from '@/shared/components/molecules/UIField';
import { UISelect } from '@/shared/components/molecules/UISelect';
import { UIButton } from '@/shared/components/atoms/UIButton';
import { UICard } from '@/shared/components/atoms/UICard';
import { UIStack } from '@/shared/components/atoms/UIStack';
import { UIText } from '@/shared/components/atoms/UIText';
import { useApi } from '@/shared/api/context';
import { t } from '@/shared/i18n/t';

import { loadFont, loadFonts, type EditorFont } from './text/fonts';
import { TEXT_PRESETS, type TextPresetName } from './text/presets';
import { rasterizeText } from './text/rasterize';
import type { TextClip, TextStyle } from './model/types';

type Props = {
  clip: TextClip | null;
  path: string;
  onAdd: (preset: TextPresetName) => void;
  onChange: (id: string, style: TextStyle) => void;
  onRasterChange: (id: string, src: string) => void;
};

function presetLabel(preset: TextPresetName): string {
  switch (preset) {
    case 'lower-third':
      return t('editor.text.preset_lower_third');
    case 'title-center':
      return t('editor.text.preset_title_center');
    case 'caption-bold':
      return t('editor.text.preset_caption_bold');
  }
}

const WEIGHTS = [100, 200, 300, 400, 500, 600, 700, 800, 900].map((weight) => ({ value: String(weight), label: String(weight) }));
const ALIGNMENTS = [
  { value: 'left', label: t('editor.text.align_left') },
  { value: 'center', label: t('editor.text.align_center') },
  { value: 'right', label: t('editor.text.align_right') },
];

/** Crea títulos y genera PNG con alfa para el visor y el render. */
export function TextInspector({ clip, path, onAdd, onChange, onRasterChange }: Props): React.JSX.Element {
  const api = useApi();
  const [preset, setPreset] = useState<TextPresetName>('lower-third');
  const [fonts, setFonts] = useState<EditorFont[]>([]);
  const [error, setError] = useState(false);
  const rasterChangeRef = useRef(onRasterChange);
  const clipId = clip?.id;
  const textSignature = clip ? JSON.stringify(clip.text) : '';

  useEffect(() => {
    rasterChangeRef.current = onRasterChange;
  }, [onRasterChange]);

  useEffect(() => {
    if (!clipId) return;
    let active = true;
    void loadFonts(api).then((available) => {
      if (active) setFonts(available);
    }).catch(() => {
      if (active) setError(true);
    });
    return () => {
      active = false;
    };
  }, [api, clipId]);

  useEffect(() => {
    if (!clipId || !textSignature) return;
    let active = true;
    const text = JSON.parse(textSignature) as TextStyle;
    const timer = window.setTimeout(() => {
      void (async () => {
        try {
          setError(false);
          await loadFont(api, text.font);
          if (!active) return;
          const raster = await rasterizeText(text);
          if (!active) return;
          const query = new URLSearchParams({ path, clip_id: clipId, sha256: raster.hash });
          const uploaded = await api.upload<{ src: string }>(`/editor/projects/media?${query}`, raster.blob, 'image/png');
          if (active) rasterChangeRef.current(clipId, uploaded.src);
        } catch {
          if (active) setError(true);
        }
      })();
    }, 200);
    return () => {
      active = false;
      window.clearTimeout(timer);
    };
  }, [api, clipId, path, textSignature]);

  function update(change: Partial<TextStyle>): void {
    if (clip) onChange(clip.id, { ...clip.text, ...change });
  }

  function updateStroke(change: Partial<TextStyle['stroke']>): void {
    if (clip) update({ stroke: { ...clip.text.stroke, ...change } });
  }

  function updateShadow(change: Partial<TextStyle['shadow']>): void {
    if (clip) update({ shadow: { ...clip.text.shadow, ...change } });
  }

  function boundedNumber(raw: string, min: number, max: number): number | null {
    if (raw.trim() === '') return null;
    const value = Number(raw);
    return Number.isFinite(value) ? Math.min(max, Math.max(min, value)) : null;
  }

  return (
    <UICard aria-label={t('editor.text.title')}>
      <UIStack gap="sm">
        <UIText variant="heading">{t('editor.text.title')}</UIText>
        {clip ? (
          <>
            <UIField label={t('editor.text.content')} value={clip.text.content} onChange={(event) => update({ content: event.currentTarget.value })} />
            <UISelect
              label={t('editor.text.font')}
              value={clip.text.font}
              options={[{ value: clip.text.font, label: clip.text.font }, ...fonts
                .filter((font) => font.family !== clip.text.font)
                .map((font) => ({ value: font.family, label: font.family }))]}
              onChange={(font) => update({ font })}
            />
            <UISelect label={t('editor.text.weight')} value={String(clip.text.weight)} options={WEIGHTS} onChange={(weight) => update({ weight: Number(weight) })} />
            <UIField label={t('editor.text.size')} type="number" min={1} max={1000} value={clip.text.size} onChange={(event) => {
              const size = boundedNumber(event.currentTarget.value, 1, 1000);
              if (size !== null) update({ size });
            }} />
            <UIField label={t('editor.text.color')} type="color" value={clip.text.color} onChange={(event) => update({ color: event.currentTarget.value })} />
            <UIField label={t('editor.text.stroke_color')} type="color" value={clip.text.stroke.color} onChange={(event) => updateStroke({ color: event.currentTarget.value })} />
            <UIField label={t('editor.text.stroke_width')} type="number" min={0} max={32} value={clip.text.stroke.width} onChange={(event) => {
              const width = boundedNumber(event.currentTarget.value, 0, 32);
              if (width !== null) updateStroke({ width });
            }} />
            <UIField label={t('editor.text.shadow_blur')} type="number" min={0} max={100} value={clip.text.shadow.blur} onChange={(event) => {
              const blur = boundedNumber(event.currentTarget.value, 0, 100);
              if (blur !== null) updateShadow({ blur });
            }} />
            <UISelect label={t('editor.text.align')} value={clip.text.align} options={ALIGNMENTS} onChange={(align) => update({ align: align as TextStyle['align'] })} />
            {error ? <UIText role="alert" variant="caption">{t('editor.text.error')}</UIText> : null}
          </>
        ) : (
          <>
            <UISelect
              label={t('editor.text.preset')}
              value={preset}
              options={TEXT_PRESETS.map((value) => ({ value, label: presetLabel(value) }))}
              onChange={(value) => setPreset(value as TextPresetName)}
            />
            <UIButton
              variant="secondary"
              draggable
              onClick={() => onAdd(preset)}
              onDragStart={(event) => {
                event.dataTransfer.setData('application/x-editor-text-preset', preset);
                event.dataTransfer.effectAllowed = 'copy';
              }}
            >
              {t('editor.text.add')}
            </UIButton>
          </>
        )}
      </UIStack>
    </UICard>
  );
}

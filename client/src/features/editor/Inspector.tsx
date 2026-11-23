import { UIIconButton } from '@/shared/components/molecules/UIIconButton';
import { UIField } from '@/shared/components/molecules/UIField';
import { UISelect } from '@/shared/components/molecules/UISelect';
import { UICard } from '@/shared/components/atoms/UICard';
import { UIStack } from '@/shared/components/atoms/UIStack';
import { UIText } from '@/shared/components/atoms/UIText';
import { t } from '@/shared/i18n/t';

import { clipProperty } from './preview/compositor';
import type { Clip, Doc, Keyframe, VisualClip } from './model/types';
import type { VisualProperty } from './model/visual';

type Props = {
  doc: Doc;
  clipId: string | null;
  time: number;
  onChange: (property: VisualProperty, value: number) => void;
  onSpeedChange: (clipId: string, speed: number) => void;
  onToggleKeyframe: (property: VisualProperty) => void;
  onEaseChange: (property: VisualProperty, ease: Keyframe['ease']) => void;
  onSeek: (time: number) => void;
  onCanvasChange: (change: Partial<Doc['canvas']>) => void;
};

const PROPERTIES: VisualProperty[] = [
  'x', 'y', 'scale_x', 'scale_y', 'rotation', 'opacity', 'anchor_x', 'anchor_y',
  'crop_l', 'crop_t', 'crop_r', 'crop_b',
];
const EASES = [
  { value: 'linear', label: t('editor.inspector.ease_linear') },
  { value: 'ease-in-out', label: t('editor.inspector.ease_in_out') },
  { value: 'hold', label: t('editor.inspector.ease_hold') },
];
const PRESETS = [
  { value: '1920x1080', label: t('editor.inspector.preset_landscape') },
  { value: '1080x1920', label: `${t('editor.inspector.preset_reels')} ★` },
  { value: '1080x1080', label: t('editor.inspector.preset_square') },
];
const PROPERTY_LABELS: Record<VisualProperty, string> = {
  x: t('editor.inspector.property_x'),
  y: t('editor.inspector.property_y'),
  scale_x: t('editor.inspector.property_scale_x'),
  scale_y: t('editor.inspector.property_scale_y'),
  rotation: t('editor.inspector.property_rotation'),
  opacity: t('editor.inspector.property_opacity'),
  anchor_x: t('editor.inspector.property_anchor_x'),
  anchor_y: t('editor.inspector.property_anchor_y'),
  crop_l: t('editor.inspector.property_crop_l'),
  crop_t: t('editor.inspector.property_crop_t'),
  crop_r: t('editor.inspector.property_crop_r'),
  crop_b: t('editor.inspector.property_crop_b'),
};

function propertyLabel(property: VisualProperty): string {
  return PROPERTY_LABELS[property];
}

function visualClip(clip: Clip | undefined): VisualClip | null {
  return clip && (clip.media === 'video' || clip.media === 'image' || clip.media === 'text') ? clip : null;
}

function limits(property: VisualProperty): { min?: number; max?: number } {
  if (property === 'scale_x' || property === 'scale_y') return { min: 0.01, max: 100 };
  if (property === 'opacity' || property.startsWith('crop_') || property.startsWith('anchor_')) return { min: 0, max: 1 };
  if (property === 'rotation') return { min: -360, max: 360 };
  return {};
}

function keyframeTimes(clip: VisualClip): number[] {
  return [...new Set(Object.values(clip.keyframes).flatMap((frames) => frames.map((frame) => clip.start + frame.t)))].sort((a, b) => a - b);
}

function activeEase(clip: VisualClip, property: VisualProperty, time: number, fps: number): Keyframe['ease'] | '' {
  const relative = time - clip.start;
  const frame = clip.keyframes[property]?.find((item) => Math.abs(item.t - relative) <= 0.5 / fps);
  return frame?.ease ?? '';
}

/** Edición numérica de propiedades, keyframes y ajustes del lienzo del proyecto. */
export function Inspector({ doc, clipId, time, onChange, onSpeedChange, onToggleKeyframe, onEaseChange, onSeek, onCanvasChange }: Props): React.JSX.Element {
  const selected = doc.clips.find((item) => item.id === clipId);
  const clip = visualClip(selected);
  const canChangeSpeed = selected && (selected.media === undefined || selected.media === 'video');
  const times = clip ? keyframeTimes(clip) : [];
  const previous = [...times].reverse().find((point) => point < time - 0.5 / doc.canvas.fps);
  const next = times.find((point) => point > time + 0.5 / doc.canvas.fps);
  const presetValue = PRESETS.some((preset) => preset.value === `${doc.canvas.width}x${doc.canvas.height}`)
    ? `${doc.canvas.width}x${doc.canvas.height}`
    : 'custom';
  const presetOptions = [...PRESETS, { value: 'custom', label: t('normalize.preset.custom') }];

  function setCanvasNumber(property: 'width' | 'height' | 'fps', raw: string): void {
    const value = Number(raw);
    if (Number.isFinite(value) && value > 0) onCanvasChange({ [property]: Math.round(value) });
  }

  function setClipSpeed(raw: string): void {
    const speed = Number(raw);
    if (canChangeSpeed && Number.isFinite(speed) && speed >= 0.25 && speed <= 4) onSpeedChange(selected.id, speed);
  }

  return (
    <UICard aria-label={t('editor.inspector.label')}>
      <UIStack gap="sm">
        <UIText variant="heading">{t('editor.inspector.label')}</UIText>
        {canChangeSpeed ? (
          <UIField
            label={t('editor.inspector.speed')}
            type="number"
            min={0.25}
            max={4}
            step="any"
            value={selected.speed ?? 1}
            onChange={(event) => setClipSpeed(event.currentTarget.value)}
          />
        ) : null}
        {clip ? (
          <>
            <UIStack direction="row" gap="xs">
              <UIIconButton icon="chevron-left" label={t('editor.inspector.previous')} disabled={previous === undefined} onClick={() => previous !== undefined && onSeek(previous)} />
              <UIIconButton icon="chevron-right" label={t('editor.inspector.next')} disabled={next === undefined} onClick={() => next !== undefined && onSeek(next)} />
            </UIStack>
            {PROPERTIES.map((property) => {
              const label = propertyLabel(property);
              const fallback = property.startsWith('crop_')
                ? clip.transform.crop[property.slice(-1) as 'l' | 't' | 'r' | 'b']
                : clip.transform[property as keyof Omit<VisualClip['transform'], 'crop'>];
              const value = clipProperty(clip, property, time, fallback);
              const ease = activeEase(clip, property, time, doc.canvas.fps);
              return (
                <UIStack key={property} direction="row" align="end" gap="xs">
                  <UIField
                    label={label}
                    type="number"
                    step="any"
                    value={value}
                    {...limits(property)}
                    onChange={(event) => {
                      const rawValue = Number(event.currentTarget.value);
                      if (!Number.isFinite(rawValue)) return;
                      const range = limits(property);
                      onChange(property, Math.min(range.max ?? Infinity, Math.max(range.min ?? -Infinity, rawValue)));
                    }}
                  />
                  <UIIconButton
                    icon="keyframe"
                    label={t('editor.inspector.keyframe', { property: label })}
                    pressed={ease !== ''}
                    onClick={() => onToggleKeyframe(property)}
                  />
                  <UISelect
                    label={t('editor.inspector.ease', { property: label })}
                    value={ease || 'linear'}
                    options={EASES}
                    disabled={ease === ''}
                    onChange={(selectedEase) => onEaseChange(property, selectedEase as Keyframe['ease'])}
                  />
                </UIStack>
              );
            })}
          </>
        ) : selected ? null : <UIText variant="caption">{t('editor.inspector.no_selection')}</UIText>}
        <UISelect
          label={t('editor.inspector.canvas_preset')}
          value={presetValue}
          options={presetOptions}
          onChange={(value) => {
            const [width, height] = value.split('x').map(Number);
            if (Number.isFinite(width) && Number.isFinite(height)) onCanvasChange({ width, height });
          }}
        />
        <UIStack direction="row" gap="xs">
          <UIField label={t('editor.inspector.canvas_width')} type="number" min={1} max={7680} value={doc.canvas.width} onChange={(event) => setCanvasNumber('width', event.currentTarget.value)} />
          <UIField label={t('editor.inspector.canvas_height')} type="number" min={1} max={7680} value={doc.canvas.height} onChange={(event) => setCanvasNumber('height', event.currentTarget.value)} />
        </UIStack>
        <UIStack direction="row" gap="xs">
        <UIField label={t('convert.advanced.fps')} type="number" min={1} max={120} value={doc.canvas.fps} onChange={(event) => setCanvasNumber('fps', event.currentTarget.value)} />
          <UIField label={t('editor.inspector.background')} type="color" value={doc.canvas.background} onChange={(event) => onCanvasChange({ background: event.currentTarget.value })} />
        </UIStack>
      </UIStack>
    </UICard>
  );
}

import { UIStack } from '@/shared/components/atoms/UIStack';

import { Inspector } from './Inspector';
import { ColorInspector } from './ColorInspector';
import { EffectsInspector } from './EffectsInspector';
import { TextInspector } from './TextInspector';
import { setKeyframeEase, toggleKeyframe, writeVisualValue } from './model/visual';
import type { BlendMode, ChromaKey, Clip, ColorEffects, Doc, Keyframe, TextClip, TextStyle, TransitionType, VisualClip } from './model/types';
import type { TextPresetName } from './text/presets';
import { Viewer } from './preview/Viewer';
import { TransitionsPanel } from './TransitionsPanel';

type Props = {
  doc: Doc;
  path: string;
  time: number;
  selectedIds: string[];
  onPreviewDoc: (doc: Doc) => void;
  onCommitPreview: () => void;
  onCancelPreview: () => void;
  onSeek: (time: number) => void;
  onAddTransition: (type: TransitionType) => void;
  onAddText: (preset: TextPresetName) => void;
};

function isVisualClip(clip: Clip): clip is VisualClip {
  return clip.media === 'image' || clip.media === 'video' || clip.media === 'text';
}

function selectedVisualId(doc: Doc, ids: string[]): string | null {
  return ids.find((id) => {
    const clip = doc.clips.find((item) => item.id === id);
    return clip !== undefined && isVisualClip(clip);
  }) ?? null;
}

function selectedClipId(doc: Doc, ids: string[]): string | null {
  return ids.find((id) => doc.clips.some((clip) => clip.id === id)) ?? null;
}

/** Visor, inspector y transiciones del editor visual. */
export function EditorVisualPanel({
  doc, path, time, selectedIds, onPreviewDoc, onCommitPreview, onCancelPreview, onSeek, onAddTransition, onAddText,
}: Props): React.JSX.Element {
  const clipId = selectedClipId(doc, selectedIds);
  const visualId = selectedVisualId(doc, selectedIds);
  const clip = doc.clips.find((item) => item.id === visualId);
  const visual = clip && isVisualClip(clip) ? clip : null;
  const textClip = clip?.media === 'text' ? clip as TextClip : null;

  function commit(next: Doc): void {
    onPreviewDoc(next);
    onCommitPreview();
  }

  function change(property: Parameters<typeof writeVisualValue>[2], value: number): void {
    if (visual) commit(writeVisualValue(doc, visual.id, property, time, value));
  }

  function toggle(property: Parameters<typeof toggleKeyframe>[2]): void {
    if (visual) commit(toggleKeyframe(doc, visual.id, property, time));
  }

  function changeEase(property: Parameters<typeof setKeyframeEase>[2], ease: Keyframe['ease']): void {
    if (visual) commit(setKeyframeEase(doc, visual.id, property, time, ease));
  }

  function changeSpeed(id: string, speed: number): void {
    const next = structuredClone(doc);
    const target = next.clips.find((item) => item.id === id);
    if (!target || (target.media !== undefined && target.media !== 'video')) return;
    const group = target.link ? next.clips.filter((item) => item.link === target.link) : [target];
    for (const member of group) {
      if (member.media === undefined || member.media === 'video') member.speed = speed;
    }
    commit(next);
  }

  function changeCanvas(changeSet: Partial<Doc['canvas']>): void {
    const next = structuredClone(doc);
    next.canvas = { ...next.canvas, ...changeSet };
    commit(next);
  }

  function changeText(id: string, style: TextStyle): void {
    const next = structuredClone(doc);
    const target = next.clips.find((item) => item.id === id);
    if (target?.media !== 'text') return;
    target.text = style;
    onPreviewDoc(next);
    onCommitPreview();
  }

  function changeTextRaster(id: string, src: string): void {
    const next = structuredClone(doc);
    const target = next.clips.find((item) => item.id === id);
    if (target?.media !== 'text') return;
    target.src = src;
    target.raster = src;
    onPreviewDoc(next);
    onCommitPreview();
  }

  function changeColor(id: string, color: ColorEffects): void {
    const next = structuredClone(doc);
    const target = next.clips.find((item): item is VisualClip => item.id === id && isVisualClip(item));
    if (!target) return;
    target.color = color;
    commit(next);
  }

  function changeEffects(id: string, changeSet: { blend_mode?: BlendMode; chroma?: ChromaKey | null }): void {
    const next = structuredClone(doc);
    const target = next.clips.find((item): item is VisualClip => item.id === id && isVisualClip(item));
    if (!target) return;
    if (changeSet.blend_mode) target.blend_mode = changeSet.blend_mode;
    if ('chroma' in changeSet) {
      if (changeSet.chroma) target.chroma = changeSet.chroma;
      else delete target.chroma;
    }
    commit(next);
  }

  return (
    <UIStack gap="sm">
      <UIStack direction="row" align="start" className="flex-col items-stretch gap-4 lg:flex-row">
        <UIStack className="min-w-0 flex-1">
          <Viewer
            doc={doc}
            path={path}
            time={time}
            selectedClipId={visualId}
            onPreviewDoc={onPreviewDoc}
            onCommitPreview={onCommitPreview}
            onCancelPreview={onCancelPreview}
          />
        </UIStack>
        <UIStack className="w-full shrink-0 lg:w-80">
          <Inspector
            doc={doc}
            clipId={clipId}
            time={time}
            onChange={change}
            onSpeedChange={changeSpeed}
            onToggleKeyframe={toggle}
            onEaseChange={changeEase}
            onSeek={onSeek}
            onCanvasChange={changeCanvas}
          />
          <ColorInspector clip={visual} path={path} onChange={changeColor} />
          <EffectsInspector clip={visual} onChange={changeEffects} />
        </UIStack>
      </UIStack>
      <TextInspector
        clip={textClip}
        path={path}
        onAdd={onAddText}
        onChange={changeText}
        onRasterChange={changeTextRaster}
      />
      <TransitionsPanel onAdd={onAddTransition} />
    </UIStack>
  );
}

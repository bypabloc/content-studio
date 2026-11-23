import { UIStack } from '@/shared/components/atoms/UIStack';

import { Inspector } from './Inspector';
import { setKeyframeEase, toggleKeyframe, writeVisualValue } from './model/visual';
import type { Doc, Keyframe, TransitionType, VisualClip } from './model/types';
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
};

function selectedVisualId(doc: Doc, ids: string[]): string | null {
  return ids.find((id) => {
    const clip = doc.clips.find((item) => item.id === id);
    return clip?.media === 'image' || clip?.media === 'video';
  }) ?? null;
}

/** Visor, inspector y transiciones del editor visual. */
export function EditorVisualPanel({
  doc, path, time, selectedIds, onPreviewDoc, onCommitPreview, onCancelPreview, onSeek, onAddTransition,
}: Props): React.JSX.Element {
  const clipId = selectedVisualId(doc, selectedIds);
  const clip = doc.clips.find((item) => item.id === clipId);
  const visual = clip && (clip.media === 'image' || clip.media === 'video') ? (clip as VisualClip) : null;

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

  function changeCanvas(changeSet: Partial<Doc['canvas']>): void {
    const next = structuredClone(doc);
    next.canvas = { ...next.canvas, ...changeSet };
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
            selectedClipId={clipId}
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
            onToggleKeyframe={toggle}
            onEaseChange={changeEase}
            onSeek={onSeek}
            onCanvasChange={changeCanvas}
          />
        </UIStack>
      </UIStack>
      <TransitionsPanel onAdd={onAddTransition} />
    </UIStack>
  );
}

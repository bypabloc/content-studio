import { useRef, useState } from 'react';
import type { PointerEvent as ReactPointerEvent } from 'react';
import type { DragEvent as ReactDragEvent } from 'react';

import { UILane } from '@/shared/components/atoms/UILane';
import { UIStack } from '@/shared/components/atoms/UIStack';
import { t } from '@/shared/i18n/t';

import { ClipView } from './ClipView';
import { Ruler } from './Ruler';
import { TrackHeader } from './TrackHeader';
import type { Levels } from '@/features/recording/capture/useRecorder';
import { pxToTime, selectInRange } from './model/timeline';
import { clipLength } from './model/validate';
import type { Doc, Op } from './model/types';

type Props = {
  doc: Doc;
  selectedIds: string[];
  playhead: number;
  zoom: number;
  magnet: boolean;
  onSelectionChange: (ids: string[]) => void;
  onPreview: (doc: Doc) => void;
  onCommitPreview: () => void;
  onCancelPreview: () => void;
  onOperation?: (op: Op) => void;
  onDropFiles?: (paths: string[], trackId: string | undefined, start: number) => void;
  armedTrackIds?: string[];
  onArmedChange?: (trackId: string, armed: boolean) => void;
  selectedMarker?: string | null;
  onMarkerSelect?: (id: string) => void;
  onMarkerRename?: (id: string, label: string) => void;
  recordingLevels?: Levels;
};

type Range = { trackId: string; anchor: number; current: number; left: number };

/** Línea de tiempo multipista con clips, selección por rango, arrastre, recorte e imán. */
export function Timeline({
  doc,
  selectedIds,
  playhead,
  zoom,
  magnet,
  onSelectionChange,
  onPreview,
  onCommitPreview,
  onCancelPreview,
  onOperation = () => undefined,
  onDropFiles,
  armedTrackIds = [],
  onArmedChange = () => undefined,
  selectedMarker = null,
  onMarkerSelect,
  onMarkerRename,
  recordingLevels,
}: Props): React.JSX.Element {
  const [range, setRange] = useState<Range | null>(null);
  const rangeRef = useRef<Range | null>(null);
  const duration = Math.max(
    10,
    ...doc.clips.map((clip) => clip.start + clipLength(clip)),
    ...doc.markers.map((marker) => marker.t),
  );
  const width = duration * zoom;

  function droppedPaths(event: ReactDragEvent<HTMLDivElement>): string[] {
    const data = event.dataTransfer.getData('application/x-content-studio-paths');
    if (!data) return [];
    try {
      const parsed: unknown = JSON.parse(data);
      return Array.isArray(parsed) ? parsed.filter((path): path is string => typeof path === 'string') : [];
    } catch {
      return [];
    }
  }

  function dropOnLane(trackId: string, event: ReactDragEvent<HTMLDivElement>): void {
    event.preventDefault();
    event.stopPropagation();
    const paths = droppedPaths(event);
    if (paths.length) {
      const left = event.currentTarget.getBoundingClientRect().left;
      onDropFiles?.(paths, trackId, pxToTime(Math.max(0, event.clientX - left), zoom));
    }
  }

  function dropOnTimeline(event: ReactDragEvent<HTMLDivElement>): void {
    event.preventDefault();
    const paths = droppedPaths(event);
    if (paths.length) onDropFiles?.(paths, undefined, playhead);
  }

  function beginRange(trackId: string, event: ReactPointerEvent<HTMLDivElement>): void {
    if (event.button !== 0) return;
    event.preventDefault();
    const left = event.currentTarget.getBoundingClientRect().left;
    const x = event.clientX - left;
    const next = { trackId, anchor: x, current: x, left };
    rangeRef.current = next;
    setRange(next);
    event.currentTarget.setPointerCapture?.(event.pointerId);
  }

  function moveRange(event: ReactPointerEvent<HTMLDivElement>): void {
    const current = rangeRef.current;
    if (!current) return;
    const next = { ...current, current: event.clientX - current.left };
    rangeRef.current = next;
    setRange(next);
  }

  function finishRange(event: ReactPointerEvent<HTMLDivElement>): void {
    const current = rangeRef.current;
    if (!current) return;
    const end = event.clientX - current.left;
    const from = pxToTime(Math.min(current.anchor, end), zoom);
    const to = pxToTime(Math.max(current.anchor, end), zoom);
    onSelectionChange(selectInRange(doc.clips, from, to));
    rangeRef.current = null;
    setRange(null);
  }

  return (
    <UIStack
      role="group"
      aria-label={t('editor.timeline.label')}
      className="min-w-0 overflow-auto"
      gap="xs"
      onDragOver={(event) => event.preventDefault()}
      onDrop={dropOnTimeline}
    >
      <UIStack direction="row" align="stretch" gap="xs">
        <UIStack aria-hidden="true" className="w-56 shrink-0" />
        <Ruler
          duration={duration}
          zoom={zoom}
          playhead={playhead}
          markers={doc.markers}
          selectedMarker={selectedMarker}
          onMarkerSelect={onMarkerSelect}
          onMarkerRename={onMarkerRename}
        />
      </UIStack>
      {doc.tracks.map((track) => {
        const isArmed = armedTrackIds.includes(track.id);
        return (
          <UIStack
            key={track.id}
            role="group"
            aria-label={t('editor.timeline.track', { name: track.name })}
            direction="row"
            align="stretch"
            gap="xs"
          >
            <TrackHeader
              track={track}
              armed={isArmed}
            levels={isArmed ? recordingLevels : undefined}
              onChange={onOperation}
              onArmedChange={(armed) => onArmedChange(track.id, armed)}
            />
            <UILane
              role="group"
              aria-label={t('editor.timeline.lane', { name: track.name })}
              className="min-w-0 shrink-0"
              style={{ width: `${width}px`, height: `${track.height}px` }}
              onPointerDown={(event) => beginRange(track.id, event)}
              onPointerMove={moveRange}
              onPointerUp={finishRange}
              onDragOver={(event) => event.preventDefault()}
              onDrop={(event) => dropOnLane(track.id, event)}
              onPointerCancel={() => {
                rangeRef.current = null;
                setRange(null);
              }}
            >
              {doc.clips
                .filter((clip) => clip.track === track.id)
                .map((clip) => (
                  <ClipView
                    key={clip.id}
                    clip={clip}
                    doc={doc}
                    selected={selectedIds.includes(clip.id)}
                    selectedIds={selectedIds}
                    zoom={zoom}
                    magnet={magnet}
                    playhead={playhead}
                    locked={track.locked}
                    onSelect={onSelectionChange}
                    onPreview={onPreview}
                    onCommitPreview={onCommitPreview}
                    onCancelPreview={onCancelPreview}
                  />
                ))}
              {range?.trackId === track.id ? (
                <UIStack
                  role="img"
                  aria-label={t('editor.timeline.range')}
                  className="pointer-events-none absolute top-0 z-20 h-full border border-primary/60 bg-primary/10"
                  style={{
                    left: `${Math.min(range.anchor, range.current)}px`,
                    width: `${Math.abs(range.current - range.anchor)}px`,
                  }}
                />
              ) : null}
            </UILane>
          </UIStack>
        );
      })}
    </UIStack>
  );
}

import { useCallback, useEffect, useRef, useState } from 'react';
import type { KeyboardEvent } from 'react';

import { useApi } from '@/shared/api/context';
import { UIStack } from '@/shared/components/atoms/UIStack';
import { UIText } from '@/shared/components/atoms/UIText';
import { UIButton } from '@/shared/components/atoms/UIButton';
import { UIRangeInput } from '@/shared/components/atoms/UIRangeInput';
import { UIIconButton } from '@/shared/components/molecules/UIIconButton';
import { t } from '@/shared/i18n/t';
import { MICROPHONE_SETTING } from '@/features/recording/microphones';
import { MicrophonePicker } from '@/features/recording/MicrophonePicker';

import { ClipMissing } from './browser/ClipMissing';
import { FileBrowser } from './browser/FileBrowser';
import { EditorVisualPanel } from './EditorVisualPanel';
import { ExportDialog } from './ExportDialog';
import { buildImportOperations } from './importMedia';
import { Timeline } from './Timeline';
import { Transport } from './Transport';
import { createTextStyle, type TextPresetName } from './text/presets';
import { duration } from './model/validate';
import { addTransitionAtCut } from './model/visual';
import type { Doc, TextClip, TransitionType } from './model/types';
import { usePlayback } from './playback/usePlayback';
import { useEditorDoc } from './useEditorDoc';
import { useTrackRecorder } from './useTrackRecorder';
import { zoomIn, zoomOut } from './model/timeline';

type Project = { path: string; hash: string; doc: Doc; missing?: string[] };
const SHORTCUTS = 'Home Space R N M S T Delete + -'; // i18n-ignore: secuencia estándar de teclas de edición

/** Espacio de trabajo del editor: explorador, captura, transporte, línea de tiempo y exportación. */
export function EditorWorkspace({
  project,
  onBack,
  autoRecord = false,
  onAutoRecordComplete = () => undefined,
}: {
  project: Project;
  onBack: () => void;
  autoRecord?: boolean;
  onAutoRecordComplete?: () => void;
}): React.JSX.Element {
  const api = useApi();
  const editor = useEditorDoc(project);
  const playback = usePlayback(editor.doc, api.fileUrl);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [armedTrackIds, setArmedTrackIds] = useState<string[]>(() =>
    autoRecord && project.doc.tracks[0] ? [project.doc.tracks[0].id] : [],
  );
  const [selectedMarker, setSelectedMarker] = useState<string | null>(null);
  const autoStarted = useRef(false);
  const [magnet, setMagnet] = useState(true);
  const [zoom, setZoom] = useState(80);
  const [deviceId, setDeviceId] = useState('');
  const [recordOffsetMs, setRecordOffsetMs] = useState(0);
  const [importError, setImportError] = useState(false);
  const armedTrackId = armedTrackIds[0] ?? null;
  const { recording, uploading, levels, error: recorderError, start: startRecording, stop: stopRecording } = useTrackRecorder({
    path: project.path,
    trackId: armedTrackId,
    playhead: playback.position,
    recordOffsetMs,
    deviceId,
    onOperation: editor.applyOp,
  });
  const applyOp = editor.applyOp;
  const trackCount = editor.doc.tracks.length;
  const saveLabel =
    editor.saveState === 'saved'
      ? t('editor.save.saved')
      : editor.saveState === 'dirty'
        ? t('editor.save.dirty')
        : editor.saveState === 'saving'
          ? t('editor.save.saving')
          : t('editor.save.error');
  const recorderErrorText =
    recorderError === 'editor.recorder.arm_track'
      ? t('editor.recorder.arm_track')
      : recorderError === 'editor.recorder.upload_error'
        ? t('editor.recorder.upload_error')
        : recorderError === 'editor.recorder.start_error'
          ? t('editor.recorder.start_error')
          : null;

  useEffect(() => {
    let active = true;
    void Promise.all([
      api.get<{ value: string | null }>(`/settings/${encodeURIComponent(MICROPHONE_SETTING)}`),
      api.get<{ value: number | null }>('/settings/editor.record_offset_ms'),
    ])
      .then(([microphone, offset]) => {
        if (!active) return;
        setDeviceId(microphone.value ?? '');
        setRecordOffsetMs(offset.value ?? 0);
      })
      .catch(() => undefined);
    return () => {
      active = false;
    };
  }, [api]);

  useEffect(() => {
    if (!autoRecord || !armedTrackId || autoStarted.current) return;
    autoStarted.current = true;
    void startRecording();
    onAutoRecordComplete();
  }, [armedTrackId, autoRecord, onAutoRecordComplete, startRecording]);

  const setTrackArmed = (trackId: string, armed: boolean) => setArmedTrackIds(armed ? [trackId] : []);

  const addFiles = useCallback(
    async (paths: string[], targetTrack: string | undefined, start: number) => {
      setImportError(false);
      try {
        const files = await Promise.all(paths.map(async (source) => {
          const info = await api.get<{
            duration: number;
            kind: 'audio' | 'video' | 'image';
            has_audio: boolean;
          }>(`/fs/info?path=${encodeURIComponent(source)}`);
          if (!Number.isFinite(info.duration) || info.duration <= 0) throw new Error('invalid duration');
          return { source, ...info };
        }));
        for (const operation of buildImportOperations(files, editor.doc.tracks, trackCount, targetTrack, start)) {
          applyOp(operation);
        }
      } catch {
        setImportError(true);
      }
    },
    [api, applyOp, editor.doc.tracks, trackCount],
  );

  function recordChange(next: boolean): void {
    if (next) void startRecording();
    else void stopRecording();
  }

  function addTransition(type: TransitionType, time = playback.position, trackId?: string): void {
    const selected = editor.doc.clips.find((clip) => selectedIds.includes(clip.id) && (clip.media === 'image' || clip.media === 'video'));
    const targetTrack = trackId ?? selected?.track ?? editor.doc.tracks.find((track) => track.kind === 'video')?.id;
    if (!targetTrack) return;
    const next = addTransitionAtCut(editor.doc, targetTrack, time, type, crypto.randomUUID());
    if (!next) return;
    editor.previewDoc(next);
    editor.commitPreview();
  }

  function addText(preset: TextPresetName, time = playback.position, targetTrackId?: string): void {
    let track = editor.doc.tracks.find((item) => item.id === targetTrackId && item.kind === 'video' && !item.locked)
      ?? editor.doc.tracks.find((item) => item.kind === 'video' && !item.locked);
    if (!track) {
      track = {
        id: crypto.randomUUID(), kind: 'video', name: t('editor.text.track_name'),
        opacity: 1, hidden: false, locked: false, height: 80,
      };
      applyOp({ type: 'addTrack', track });
    }
    const id = crypto.randomUUID();
    const src = `media/text-${id}-pending.png`;
    const text: TextClip = {
      id, track: track.id, src, raster: src, media: 'text', text: createTextStyle(preset),
      src_in: 0, src_out: 5, start: Math.max(0, Number.isFinite(time) ? time : playback.position), fade_in: 0, fade_out: 0, speed: 1,
      color: { brightness: 0, contrast: 1, saturation: 1, gamma: 1 }, blend_mode: 'normal',
      transform: {
        x: 0,
        y: preset === 'lower-third' ? editor.doc.canvas.height * 0.3 : preset === 'caption-bold' ? editor.doc.canvas.height * 0.34 : 0,
        scale_x: 1, scale_y: 1, rotation: 0, opacity: 1,
        crop: { l: 0, t: 0, r: 0, b: 0 }, anchor_x: 0.5, anchor_y: 0.5,
      },
      keyframes: {},
    };
    applyOp({ type: 'addClip', clip: text });
    setSelectedIds([id]);
  }

  function onKeyDown(event: KeyboardEvent<HTMLDivElement>): void {
    if (event.defaultPrevented || event.repeat || (event.target as HTMLElement).closest('input,textarea,select')) return;
    const key = event.key.toLowerCase();
    if (event.key === 'Home') playback.seek(0);
    else if (event.key === ' ' || event.key === 'Spacebar') playback.setPlaying(!playback.playing);
    else if (key === 'r') recordChange(!recording);
    else if (key === 'n') setMagnet((current) => !current);
    else if (key === 'm') {
      applyOp({
        type: 'addMarker',
        marker: {
          id: crypto.randomUUID(),
          t: playback.position,
          label: t('editor.marker.default_name', { n: editor.doc.markers.length + 1 }),
          color: '#ef4444',
        },
      });
    } else if (key === 's') {
      applyOp({ type: 'splitAt', t: playback.position, ...(selectedIds.length ? { ids: selectedIds } : {}) });
    } else if (event.key === 'Delete' && selectedMarker) {
      applyOp({ type: 'deleteMarker', id: selectedMarker });
      setSelectedMarker(null);
    } else if (event.key === 'Delete' && selectedIds.length) {
      applyOp({ type: 'deleteClips', ids: selectedIds, ripple: event.shiftKey });
      setSelectedIds([]);
    } else if (key === 't') {
      addTransition('fade');
    } else if (event.key === '+' || event.key === '=') setZoom((current) => zoomIn(current));
    else if (event.key === '-' || event.key === '_') setZoom((current) => zoomOut(current));
    else return;
    event.preventDefault();
  }

  function relink(from: string, to: string): void {
    editor.applyOp({ type: 'replaceSource', from, to });
  }

  const missing = (project.missing ?? []).filter((source) => editor.doc.clips.some((clip) => clip.src === source));

  return (
    <UIStack
      role="region"
      aria-label={t('editor.project.workspace', { name: editor.doc.name })}
      aria-keyshortcuts={SHORTCUTS}
      tabIndex={0}
      onKeyDown={onKeyDown}
      gap="sm"
    >
      <UIStack direction="row" align="center" justify="between" gap="sm">
        <UIButton variant="secondary" icon="chevron-left" onClick={onBack}>{t('subtitles.home.back')}</UIButton>
        <UIText variant="heading">{editor.doc.name}</UIText>
        <UIText variant="caption" aria-live="polite">
          {saveLabel}{editor.saveError ? `: ${editor.saveError}` : ''}
        </UIText>
      </UIStack>
      <UIStack direction="row" align="center" gap="xs">
        <UIIconButton icon="history" label={t('editor.history.undo')} shortcut="Ctrl+Z" aria-keyshortcuts="Control+Z" disabled={!editor.canUndo} onClick={editor.undo} />
        <UIIconButton icon="regenerate" label={t('editor.history.redo')} shortcut="Ctrl+Y" aria-keyshortcuts="Control+Y" disabled={!editor.canRedo} onClick={editor.redo} />
        <Transport
          playing={playback.playing} recording={recording || uploading} magnet={magnet} zoom={zoom}
          onStart={() => playback.seek(0)} onPlayingChange={playback.setPlaying} onStop={playback.stop}
          onRecordingChange={recordChange} onMagnetChange={setMagnet} onZoomChange={setZoom}
        />
        <ExportDialog path={project.path} duration={duration(editor.doc)} markers={editor.doc.markers} />
      </UIStack>
      {missing.map((source) => <ClipMissing key={source} src={source} onRelink={relink} />)}
      {recorderErrorText ? <UIText variant="caption">{recorderErrorText}</UIText> : null}
      {uploading ? <UIText variant="caption">{t('editor.recorder.uploading')}</UIText> : null}
      {importError ? <UIText variant="caption">{t('editor.import.error')}</UIText> : null}
      <UIStack direction="row" className="flex-col items-start gap-4 lg:flex-row">
        <UIStack className="w-full shrink-0 lg:w-80" gap="sm">
          <FileBrowser onImport={(paths) => void addFiles(paths, armedTrackId ?? undefined, playback.position)} />
          <MicrophonePicker
            value={deviceId}
            onChange={(value) => {
              setDeviceId(value);
              void api.put(`/settings/${encodeURIComponent(MICROPHONE_SETTING)}`, { value });
            }}
          />
          <UIRangeInput
            aria-label={t('editor.recorder.offset')}
            label={t('editor.recorder.offset')}
            value={recordOffsetMs}
            min={-200}
            max={200}
            step={1}
            onValueChange={(value) => {
              setRecordOffsetMs(value);
              void api.put('/settings/editor.record_offset_ms', { value });
            }}
          />
        </UIStack>
        <UIStack className="min-w-0 flex-1" gap="sm">
          <EditorVisualPanel
            doc={editor.doc} path={project.path} time={playback.position} selectedIds={selectedIds}
            onPreviewDoc={editor.previewDoc} onCommitPreview={editor.commitPreview}
            onCancelPreview={editor.cancelPreview} onSeek={playback.seek} onAddTransition={addTransition}
            onAddText={addText}
          />
          <Timeline
            doc={editor.doc} selectedIds={selectedIds} playhead={playback.position} zoom={zoom} magnet={magnet}
            onSelectionChange={setSelectedIds} onPreview={editor.previewDoc} onCommitPreview={editor.commitPreview}
            onCancelPreview={editor.cancelPreview} onOperation={editor.applyOp}
            onDropFiles={(paths, track, start) => void addFiles(paths, track, start)}
            onDropTransition={(type, track, time) => addTransition(type, time, track)}
            onDropText={(preset, track, time) => addText(preset, time, track)}
            armedTrackIds={armedTrackIds} onArmedChange={setTrackArmed} onMarkerSelect={setSelectedMarker}
            onMarkerRename={(id, label) => applyOp({ type: 'renameMarker', id, label })}
            selectedMarker={selectedMarker} recordingLevels={levels}
          />
        </UIStack>
      </UIStack>
    </UIStack>
  );
}

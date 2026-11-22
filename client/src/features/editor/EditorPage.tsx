import { useEffect, useState } from 'react';
import type { KeyboardEvent } from 'react';

import { useApi } from '@/shared/api/context';
import { UIButton } from '@/shared/components/atoms/UIButton';
import { UIStack } from '@/shared/components/atoms/UIStack';
import { UIText } from '@/shared/components/atoms/UIText';
import { UIIconButton } from '@/shared/components/molecules/UIIconButton';
import { t } from '@/shared/i18n/t';

import { Timeline } from './Timeline';
import { Transport } from './Transport';
import { zoomIn, zoomOut } from './model/timeline';
import type { Doc } from './model/types';
import { usePlayback } from './playback/usePlayback';
import { useEditorDoc } from './useEditorDoc';

type Project = { path: string; hash: string; doc: Doc; missing?: string[] };
const EDITOR_SHORTCUTS = 'Home Space R N + -'; // i18n-ignore: secuencia estándar de teclas de acceso rápido

function recentName(path: string): string {
  return path.split(/[\\/]/).filter(Boolean).at(-2) ?? path;
}

/** Inicio del editor: proyectos recientes y el flujo multipista al abrir uno. */
export function EditorPage(): React.JSX.Element {
  const api = useApi();
  const [recent, setRecent] = useState<string[] | null>(null);
  const [project, setProject] = useState<Project | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    void api
      .get<{ paths: string[] }>('/editor/projects/recent')
      .then(({ paths }) => {
        if (active) setRecent(paths);
      })
      .catch(() => {
        if (active) {
          setRecent([]);
          setError(t('editor.project.load_error'));
        }
      });
    return () => {
      active = false;
    };
  }, [api]);

  async function open(path: string): Promise<void> {
    setBusy(true);
    setError(null);
    try {
      setProject(await api.get<Project>(`/editor/projects?path=${encodeURIComponent(path)}`));
    } catch {
      setError(t('editor.project.load_error'));
    } finally {
      setBusy(false);
    }
  }

  async function create(): Promise<void> {
    setBusy(true);
    setError(null);
    try {
      const created = await api.post<Project>('/editor/projects', { name: t('editor.project.default_name') });
      setRecent((paths) => [created.path, ...(paths ?? []).filter((path) => path !== created.path)]);
      setProject(created);
    } catch {
      setError(t('editor.project.load_error'));
    } finally {
      setBusy(false);
    }
  }

  if (project) return <EditorWorkspace key={project.path} project={project} onBack={() => setProject(null)} />;

  return (
    <UIStack gap="md">
      <UIButton onClick={() => void create()} disabled={busy} loading={busy}>
        {t('editor.project.create')}
      </UIButton>
      {recent === null ? (
        <UIText variant="caption">{t('editor.project.loading')}</UIText>
      ) : recent.length === 0 ? (
        <UIText variant="caption">{t('editor.project.empty')}</UIText>
      ) : (
        <UIStack role="list" aria-label={t('editor.project.recent')} gap="sm">
          {recent.map((path) => {
            const name = recentName(path);
            return (
              <UIStack key={path} role="listitem">
                <UIButton variant="secondary" aria-label={t('editor.project.open', { name })} onClick={() => void open(path)} disabled={busy}>
                  {name}
                </UIButton>
              </UIStack>
            );
          })}
        </UIStack>
      )}
      {error ? <UIText variant="caption">{error}</UIText> : null}
    </UIStack>
  );
}

function EditorWorkspace({ project, onBack }: { project: Project; onBack: () => void }): React.JSX.Element {
  const api = useApi();
  const editor = useEditorDoc(project);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [armedTrackIds, setArmedTrackIds] = useState<string[]>([]);
  const playback = usePlayback(editor.doc, api.fileUrl);
  const [recording, setRecording] = useState(false);
  const [magnet, setMagnet] = useState(true);
  const [zoom, setZoom] = useState(80);
  const saveLabel =
    editor.saveState === 'saved'
      ? t('editor.save.saved')
      : editor.saveState === 'dirty'
        ? t('editor.save.dirty')
        : editor.saveState === 'saving'
          ? t('editor.save.saving')
          : t('editor.save.error');

  function setTrackArmed(trackId: string, armed: boolean): void {
    setArmedTrackIds((current) =>
      armed ? [...new Set([...current, trackId])] : current.filter((candidate) => candidate !== trackId),
    );
  }

  function onKeyDown(event: KeyboardEvent<HTMLDivElement>): void {
    if (event.defaultPrevented || event.repeat) return;
    const key = event.key.toLowerCase();
    if (event.key === 'Home') playback.seek(0);
    else if (event.key === ' ' || event.key === 'Spacebar') playback.setPlaying(!playback.playing);
    else if (key === 'r') setRecording((current) => !current);
    else if (key === 'n') setMagnet((current) => !current);
    else if (event.key === '+' || event.key === '=') setZoom((current) => zoomIn(current));
    else if (event.key === '-' || event.key === '_') setZoom((current) => zoomOut(current));
    else return;
    event.preventDefault();
  }

  return (
    <UIStack
      role="region"
      aria-label={t('editor.project.workspace', { name: editor.doc.name })}
      aria-keyshortcuts={EDITOR_SHORTCUTS}
      tabIndex={0}
      onKeyDown={onKeyDown}
      gap="sm"
    >
      <UIStack direction="row" align="center" justify="between" gap="sm">
        <UIButton variant="secondary" icon="chevron-left" onClick={onBack}>
          {t('editor.project.back')}
        </UIButton>
        <UIText variant="heading">{editor.doc.name}</UIText>
        <UIStack aria-live="polite">
          <UIText variant="caption">
            {saveLabel}
            {editor.saveError ? `: ${editor.saveError}` : ''}
          </UIText>
        </UIStack>
      </UIStack>
      <UIStack direction="row" align="center" gap="xs">
        <UIIconButton
          icon="history"
          label={t('editor.history.undo')}
          shortcut="Ctrl+Z"
          aria-keyshortcuts="Control+Z"
          disabled={!editor.canUndo}
          onClick={editor.undo}
        />
        <UIIconButton
          icon="regenerate"
          label={t('editor.history.redo')}
          shortcut="Ctrl+Y"
          aria-keyshortcuts="Control+Y"
          disabled={!editor.canRedo}
          onClick={editor.redo}
        />
        <Transport
          playing={playback.playing}
          recording={recording}
          magnet={magnet}
          zoom={zoom}
          onStart={() => playback.seek(0)}
          onPlayingChange={playback.setPlaying}
          onStop={playback.stop}
          onRecordingChange={setRecording}
          onMagnetChange={setMagnet}
          onZoomChange={setZoom}
        />
      </UIStack>
      <Timeline
        doc={editor.doc}
        selectedIds={selectedIds}
        playhead={playback.position}
        zoom={zoom}
        magnet={magnet}
        onSelectionChange={setSelectedIds}
        onPreview={editor.previewDoc}
        onCommitPreview={editor.commitPreview}
        onCancelPreview={editor.cancelPreview}
        onOperation={editor.applyOp}
        armedTrackIds={armedTrackIds}
        onArmedChange={setTrackArmed}
      />
    </UIStack>
  );
}

import { useCallback, useEffect, useState } from 'react';

import { open as openDialog } from '@tauri-apps/plugin-dialog';

import { useApi } from '@/shared/api/context';
import { UIButton } from '@/shared/components/atoms/UIButton';
import { UIStack } from '@/shared/components/atoms/UIStack';
import { UIText } from '@/shared/components/atoms/UIText';
import { t } from '@/shared/i18n/t';
import { hashParams } from '@/shared/navigation/hash';
import { useEditorAdd } from './useEditorAdd';

import { EditorWorkspace } from './EditorWorkspace';
import type { Doc } from './model/types';

type Project = { path: string; hash: string; doc: Doc; missing?: string[] };

function recentName(path: string): string {
  return path.split(/[\\/]/).filter(Boolean).at(-2) ?? path;
}

function projectFile(folder: string): string {
  const path = folder.replace(/[\\/]+$/, '');
  const separator = folder.includes('\\') ? '\\' : '/';
  return `${path}${separator}project.json`;
}

/** Inicio del editor: proyectos recientes y opciones para crear, abrir o grabar. */
export function EditorPage(): React.JSX.Element {
  const api = useApi();
  const pendingAdd = useEditorAdd();
  const [recent, setRecent] = useState<string[] | null>(null);
  const [project, setProject] = useState<Project | null>(null);
  const [autoRecord, setAutoRecord] = useState(false);
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

  // Un `?project=` en el hash abre ese proyecto al montar: así llega Hablantes (spec 037, AC-6).
  useEffect(() => {
    const requested = hashParams().get('project');
    if (requested) void open(requested);
    // Solo al montar: el hash se lee una vez, como el resto de los parámetros de sección.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function open(path: string): Promise<void> {
    setBusy(true);
    setError(null);
    setAutoRecord(false);
    try {
      setProject(await api.get<Project>(`/editor/projects?path=${encodeURIComponent(path)}`));
    } catch {
      setError(t('editor.project.load_error'));
    } finally {
      setBusy(false);
    }
  }

  async function openFolder(): Promise<void> {
    try {
      const folder = await openDialog({ directory: true, multiple: false });
      if (typeof folder === 'string') await open(projectFile(folder));
    } catch {
      setError(t('editor.project.load_error'));
    }
  }

  const create = useCallback(async (record = false): Promise<void> => {
    try {
      const created = await api.post<Project>('/editor/projects', { name: t('editor.project.default_name') });
      setRecent((paths) => [created.path, ...(paths ?? []).filter((path) => path !== created.path)]);
      setAutoRecord(record);
      setProject(created);
    } catch {
      setError(t('editor.project.load_error'));
    } finally {
      setBusy(false);
    }
  }, [api]);

  function startCreate(record = false): void {
    setBusy(true);
    setError(null);
    void create(record);
  }

  useEffect(() => {
    if (!pendingAdd.paths.length || project) return;
    let active = true;
    void Promise.resolve().then(() => {
      if (active) void create();
    });
    return () => {
      active = false;
    };
  }, [create, pendingAdd.paths, project]);

  const creatingFromAdd = pendingAdd.paths.length > 0 && project === null;

  if (project) {
    return (
      <EditorWorkspace
        key={project.path}
        project={project}
        onBack={() => setProject(null)}
        autoRecord={autoRecord}
        onAutoRecordComplete={() => setAutoRecord(false)}
        pendingAdd={pendingAdd.paths}
        onAddHandled={pendingAdd.clear}
      />
    );
  }

  return (
    <UIStack gap="md">
      <UIStack direction="row" gap="sm">
        <UIButton onClick={() => startCreate()} disabled={busy || creatingFromAdd} loading={busy || creatingFromAdd}>
          {t('mix.create')}
        </UIButton>
        <UIButton variant="secondary" icon="open-folder" onClick={() => void openFolder()} disabled={busy}>
          {t('editor.project.open_file')}
        </UIButton>
        <UIButton
          variant="secondary"
          icon="record"
          onClick={() => startCreate(true)}
          disabled={busy || creatingFromAdd}
          loading={busy || creatingFromAdd}
        >
          {t('voices.record.start')}
        </UIButton>
      </UIStack>
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
                <UIButton
                  variant="secondary"
                  aria-label={t('editor.project.open', { name })}
                  onClick={() => void open(path)}
                  disabled={busy}
                >
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

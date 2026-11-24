import { useMutation, useQueryClient } from '@tanstack/react-query';
import { open } from '@tauri-apps/plugin-dialog';
import { useState } from 'react';

import { useApi } from '@/shared/api/context';
import { UIButton } from '@/shared/components/atoms/UIButton';
import { UIStack } from '@/shared/components/atoms/UIStack';
import { UIText } from '@/shared/components/atoms/UIText';
import { UIField } from '@/shared/components/molecules/UIField';
import { UIIconButton } from '@/shared/components/molecules/UIIconButton';
import { toast } from '@/shared/components/molecules/UIToast';
import { UIFormDialog } from '@/shared/components/organisms/UIFormDialog';
import { t } from '@/shared/i18n/t';

import type { Scope } from './types';
import { useFolders, useProjects } from './useLibrary';

interface Props {
  scope: Scope;
  onScope: (scope: Scope) => void;
  /** Tras agregar una carpeta se escanea. */
  onAdded: () => void;
}

const same = (a: Scope, b: Scope) => JSON.stringify(a) === JSON.stringify(b);

/** El panel lateral (D-6): Todo, Generado, las carpetas vigiladas, los proyectos y Espacio. */
export function FolderSidebar({ scope, onScope, onAdded }: Props): React.JSX.Element {
  const api = useApi();
  const queryClient = useQueryClient();
  const folders = useFolders();
  const projects = useProjects();
  const [naming, setNaming] = useState(false);
  const [name, setName] = useState('');
  const refresh = () => void queryClient.invalidateQueries({ queryKey: ['library'] });
  const addFolder = useMutation({
    mutationFn: (path: string) => api.post('/library/folders', { path }),
    onSuccess: () => {
      refresh();
      onAdded();
    },
    onError: (error: Error) => toast.error(error.message),
  });
  const removeFolder = useMutation({ mutationFn: (id: number) => api.del(`/library/folders/${id}`), onSuccess: refresh });
  const createProject = useMutation({
    mutationFn: () => api.post('/projects', { name }),
    onSuccess: () => {
      setNaming(false);
      setName('');
      refresh();
    },
    onError: (error: Error) => toast.error(error.message),
  });
  async function pickFolder(): Promise<void> {
    const chosen = await open({ directory: true, multiple: false, title: t('library.folders.add') });
    if (typeof chosen === 'string') addFolder.mutate(chosen);
  }
  const entry = (target: Scope, label: string) => (
    <UIButton key={JSON.stringify(target)} variant={same(scope, target) ? 'primary' : 'ghost'} aria-pressed={same(scope, target)} onClick={() => onScope(target)}>
      {label}
    </UIButton>
  );

  return (
    <UIStack role="navigation" aria-label={t('library.sidebar')} gap="sm" className="lg:w-60 lg:shrink-0">
      {entry({ type: 'all' }, t('library.scope.all'))}
      {entry({ type: 'generated' }, t('library.scope.generated'))}
      <UIText variant="caption">{t('library.folders')}</UIText>
      {(folders.data ?? []).map((folder) => (
        <UIStack key={folder.id} direction="row" gap="sm" align="center">
          {entry({ type: 'folder', id: folder.id }, folder.name ?? folder.path)}
          <UIIconButton icon="remove" label={t('library.folders.remove', { name: folder.name ?? folder.path })} onClick={() => removeFolder.mutate(folder.id)} />
        </UIStack>
      ))}
      <UIButton variant="secondary" icon="folder-plus" onClick={() => void pickFolder()}>
        {t('library.folders.add')}
      </UIButton>
      <UIText variant="caption">{t('library.projects')}</UIText>
      {(projects.data ?? []).map((project) => entry({ type: 'project', id: project.id }, t('library.projects.item', { name: project.name, count: project.count })))}
      <UIButton variant="secondary" icon="plus" onClick={() => setNaming(true)}>
        {t('library.projects.new')}
      </UIButton>
      {entry({ type: 'storage' }, t('library.scope.storage'))}
      <UIFormDialog
        open={naming}
        onOpenChange={setNaming}
        title={t('library.projects.new')}
        description={t('library.projects.new.hint')}
        confirmLabel={t('action.create')}
        cancelLabel={t('action.cancel')}
        confirmDisabled={!name.trim()}
        pending={createProject.isPending}
        onSubmit={() => createProject.mutate()}
      >
        <UIField label={t('library.projects.name')} value={name} onChange={(event) => setName(event.target.value)} />
      </UIFormDialog>
    </UIStack>
  );
}

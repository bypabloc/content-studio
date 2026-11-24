import { useMutation, useQueryClient } from '@tanstack/react-query';
import { open } from '@tauri-apps/plugin-dialog';
import { openPath } from '@tauri-apps/plugin-opener';
import { useState } from 'react';

import { useApi } from '@/shared/api/context';
import { UIButton } from '@/shared/components/atoms/UIButton';
import { UICheckbox } from '@/shared/components/atoms/UICheckbox';
import { UIStack } from '@/shared/components/atoms/UIStack';
import { UIField } from '@/shared/components/molecules/UIField';
import { UIIconButton } from '@/shared/components/molecules/UIIconButton';
import { toast } from '@/shared/components/molecules/UIToast';
import { UIFormDialog } from '@/shared/components/organisms/UIFormDialog';
import { t } from '@/shared/i18n/t';
import { openSection } from '@/shared/navigation/hash';
import { openInEditor } from '@/shared/navigation/sendTo';

import { sendLabel } from './query';
import type { LibraryItem } from './types';

/** Las secciones a las que se puede mandar cada medio (D-4); el Editor agrega el archivo a una pista nueva. */
const DESTINATIONS: Record<string, string[]> = {
  audio: ['cleaner', 'subtitles', 'convert', 'normalize', 'mix', 'editor'],
  video: ['cleaner', 'subtitles', 'convert', 'mix', 'editor'],
};

function sendTo(section: string, path: string): void {
  if (section === 'editor') openInEditor([path]);
  else openSection(section, { path });
}

interface Props {
  item: LibraryItem;
  hasJob: boolean;
  onDone: () => void;
}

/** Mandar a…, abrir carpeta, renombrar, mover y borrar (con la papelera de Windows). */
export function ItemActions({ item, hasJob, onDone }: Props): React.JSX.Element {
  const api = useApi();
  const queryClient = useQueryClient();
  const [renaming, setRenaming] = useState(false);
  const [name, setName] = useState(item.name);
  const [deleting, setDeleting] = useState(false);
  const [files, setFiles] = useState(false);
  const [wholeJob, setWholeJob] = useState(false);
  const [ignore, setIgnore] = useState(false);
  const refresh = () => void queryClient.invalidateQueries({ queryKey: ['library'] });
  const onError = (error: Error) => toast.error(error.message);
  const rename = useMutation({
    mutationFn: () => api.post(`/library/${item.id}/rename`, { name }),
    onSuccess: () => {
      setRenaming(false);
      refresh();
    },
    onError,
  });
  const move = useMutation({ mutationFn: (folder: string) => api.post(`/library/${item.id}/move`, { folder }), onSuccess: refresh, onError });
  const remove = useMutation({
    mutationFn: () => api.post(`/library/${item.id}/delete`, { files, whole_job: files && wholeJob, ignore: !files && ignore }),
    onSuccess: () => {
      setDeleting(false);
      refresh();
      onDone();
    },
    onError,
  });
  async function pickFolder(): Promise<void> {
    const folder = await open({ directory: true, multiple: false, title: t('library.move') });
    if (typeof folder === 'string') move.mutate(folder);
  }
  const folder = item.path.replace(/[\\/][^\\/]*$/, '');
  return (
    <UIStack gap="md">
      <UIStack role="group" aria-label={t('library.send_to')} direction="row" gap="sm" className="flex-wrap">
        {(DESTINATIONS[item.media_type] ?? []).map((section) => (
          <UIButton
            key={section}
            variant="secondary"
            icon="send"
            onClick={() => {
              onDone();
              sendTo(section, item.path);
            }}
          >
            {sendLabel(section)}
          </UIButton>
        ))}
      </UIStack>
      <UIStack direction="row" gap="sm" className="flex-wrap">
        <UIIconButton icon="open-folder" label={t('media.action.folder')} onClick={() => void openPath(folder)} />
        <UIButton variant="secondary" icon="pencil" onClick={() => setRenaming(true)}>{t('library.rename')}</UIButton>
        <UIButton variant="secondary" icon="open-folder" onClick={() => void pickFolder()}>{t('library.move')}</UIButton>
        <UIButton variant="danger" icon="remove" onClick={() => setDeleting(true)}>{t('library.delete')}</UIButton>
      </UIStack>
      <UIFormDialog
        open={renaming}
        onOpenChange={setRenaming}
        title={t('library.rename')}
        description={t('library.rename.hint')}
        confirmLabel={t('library.rename')}
        cancelLabel={t('action.cancel')}
        confirmDisabled={!name.trim()}
        pending={rename.isPending}
        onSubmit={() => rename.mutate()}
      >
        <UIField label={t('library.rename.name')} value={name} onChange={(event) => setName(event.target.value)} />
      </UIFormDialog>
      <UIFormDialog
        open={deleting}
        onOpenChange={setDeleting}
        title={t('library.delete.title', { name: item.name })}
        description={t('library.delete.hint')}
        confirmLabel={t('library.delete')}
        cancelLabel={t('action.cancel')}
        destructive
        pending={remove.isPending}
        onSubmit={() => remove.mutate()}
      >
        <UICheckbox label={t('library.delete.files')} checked={files} onChange={setFiles} />
        {files && hasJob ? <UICheckbox label={t('library.delete.whole_job')} checked={wholeJob} onChange={setWholeJob} /> : null}
        {!files && item.origin === 'watched' ? <UICheckbox label={t('library.delete.ignore')} checked={ignore} onChange={setIgnore} /> : null}
      </UIFormDialog>
    </UIStack>
  );
}

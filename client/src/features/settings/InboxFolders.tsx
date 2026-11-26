import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { open } from '@tauri-apps/plugin-dialog';
import { useState } from 'react';
import { useApi } from '@/shared/api/context';
import type { components } from '@/shared/api/schema';
import { UIButton } from '@/shared/components/atoms/UIButton';
import { UIStack } from '@/shared/components/atoms/UIStack';
import { UIText } from '@/shared/components/atoms/UIText';
import { UISwitch } from '@/shared/components/atoms/UISwitch';
import { UISelect } from '@/shared/components/molecules/UISelect';
import { t } from '@/shared/i18n/t';

type InboxFolder = components['schemas']['InboxFolder'];

/** Lo que hace la carpeta con cada archivo que se suelta: hoy, convertirlo a MP3 (spec 030, 02 §4.2). */
const MP3 = { kind: 'media.convert', params: { target: 'mp3' } };

/**
 * Ajustes > Integraciones (spec 030, AC-9): las carpetas de entrada. Se agregan con su carpeta, su operación y si
 * mantienen el server encendido; se pausan y se quitan. Quitar una carpeta no borra sus archivos.
 */
export function InboxFolders() {
  const api = useApi();
  const queryClient = useQueryClient();
  const [picked, setPicked] = useState('');
  const [keepAwake, setKeepAwake] = useState(true);
  const [error, setError] = useState('');
  const folders = useQuery({
    queryKey: ['inbox', 'folders'],
    queryFn: () => api.get<InboxFolder[]>('/inbox/folders'),
  });
  const refresh = () => queryClient.invalidateQueries({ queryKey: ['inbox', 'folders'] });
  const list = Array.isArray(folders.data) ? folders.data : [];

  const add = useMutation({
    mutationFn: () => api.post<InboxFolder>('/inbox/folders', { path: picked, ...MP3, keep_awake: keepAwake }),
    onSuccess: () => {
      setPicked('');
      setError('');
      void refresh();
    },
    onError: (failure: Error) => setError(failure.message),
  });

  const setPaused = useMutation({
    mutationFn: ({ id, paused }: { id: number; paused: boolean }) =>
      api.post<InboxFolder>(`/inbox/folders/${id}/pause`, { paused }),
    onSuccess: () => refresh(),
  });

  const remove = useMutation({
    mutationFn: (id: number) => api.del<void>(`/inbox/folders/${id}`),
    onSuccess: () => refresh(),
  });

  const pick = async () => {
    const chosen = await open({ directory: true, multiple: false, title: t('settings.inbox.pick') });
    if (typeof chosen === 'string') setPicked(chosen);
  };

  const operations = [{ value: 'mp3', label: t('settings.inbox.convert_mp3') }];

  return (
    <UIStack gap="md">
      <UIText variant="heading">{t('settings.inbox.title')}</UIText>
      <UIText variant="caption">{t('settings.inbox.help')}</UIText>
      {folders.isSuccess && list.length === 0 && <UIText variant="caption">{t('settings.inbox.empty')}</UIText>}
      {list.map((folder) => (
        <UIStack key={folder.id} gap="xs">
          <UIText variant="body">{folder.path}</UIText>
          <UIText variant="caption">{folder.paused ? t('settings.inbox.paused') : t('settings.inbox.active')}</UIText>
          <UIStack gap="sm">
            <UIButton
              variant="secondary"
              className="self-start"
              onClick={() => setPaused.mutate({ id: folder.id, paused: !folder.paused })}
            >
              {folder.paused ? t('settings.inbox.resume') : t('settings.inbox.pause')}
            </UIButton>
            <UIButton
              variant="danger"
              className="self-start"
              onClick={() => {
                if (window.confirm(t('settings.inbox.remove_confirm'))) remove.mutate(folder.id);
              }}
            >
              {t('settings.inbox.remove')}
            </UIButton>
          </UIStack>
        </UIStack>
      ))}
      <UIStack gap="sm">
        <UIButton variant="secondary" className="self-start" onClick={() => void pick()}>
          {t('settings.inbox.pick')}
        </UIButton>
        {picked && <UIText variant="body">{picked}</UIText>}
        <UISelect label={t('settings.inbox.operation')} options={operations} defaultValue="mp3" />
        <UISwitch
          label={t('settings.inbox.keep_awake')}
          checked={keepAwake}
          onChange={setKeepAwake}
          variant="inline"
        />
        <UIButton className="self-start" disabled={!picked || add.isPending} onClick={() => add.mutate()}>
          {t('settings.inbox.add')}
        </UIButton>
        {error && <UIText variant="caption">{error}</UIText>}
      </UIStack>
    </UIStack>
  );
}

import { useMutation } from '@tanstack/react-query';
import { useState } from 'react';

import { useApi } from '@/shared/api/context';
import { UIButton } from '@/shared/components/atoms/UIButton';
import { UICard } from '@/shared/components/atoms/UICard';
import { UIStack } from '@/shared/components/atoms/UIStack';
import { UIText } from '@/shared/components/atoms/UIText';
import { UISelect } from '@/shared/components/molecules/UISelect';
import { toast } from '@/shared/components/molecules/UIToast';
import { t } from '@/shared/i18n/t';
import { hashParams, openSection } from '@/shared/navigation/hash';

import { MixEditor } from './MixEditor';
import { MixSlot } from './MixSlot';
import type { MixProject, SlotKey } from './types';

const SLOTS: SlotKey[] = ['voice', 'music', 'video'];

/**
 * La sección Mezcla (spec 016, D-4): tres ranuras (voz, música y un video opcional) y «Crear proyecto». Con el
 * proyecto creado, abre su editor: la línea de tiempo del ducking, la vista previa y el render.
 */
export function MixPage(): React.JSX.Element {
  const api = useApi();
  const [picked, setPicked] = useState<Record<SlotKey, string | null>>(() => {
    // «Mandar a Mezclar» (narración o música) llega con la ruta en el hash: `#/mix?voice=…` o `#/mix?music=…`.
    const params = hashParams();
    return { voice: params.get('voice'), music: params.get('music'), video: params.get('video') };
  });
  const [videoMode, setVideoMode] = useState<'replace' | 'under'>('replace');
  const [projectId, setProjectId] = useState<number | null>(null);
  const ready = picked.voice !== null && picked.music !== null;

  const create = useMutation({
    mutationFn: () =>
      api.post<MixProject>('/mix/prepare', {
        voice: picked.voice,
        music: picked.music,
        video: picked.video,
        video_mode: videoMode,
      }),
    onSuccess: (project) => setProjectId(project.id),
    // El server rechaza una ruta que no sirve o un modo que no existe: el aviso lleva el texto del catálogo.
    onError: (error: Error) => toast.error(error.message),
  });

  if (projectId !== null) {
    return (
      <UIStack gap="md">
        <UIButton variant="secondary" onClick={() => setProjectId(null)}>
          {t('mix.back')}
        </UIButton>
        <MixEditor projectId={projectId} />
      </UIStack>
    );
  }

  return (
    <UIStack gap="lg">
      <UICard>
        <UIText variant="subtitle">{t('mix.title')}</UIText>
        {SLOTS.map((slot) => (
          <MixSlot
            key={slot}
            slot={slot}
            value={picked[slot]}
            onPick={(path) => setPicked((current) => ({ ...current, [slot]: path }))}
          />
        ))}
        {picked.video !== null ? (
          <UISelect
            label={t('mix.video.mode.label')}
            value={videoMode}
            options={[
              { value: 'replace', label: t('mix.video.replace') },
              { value: 'under', label: t('mix.video.under') },
            ]}
            onChange={(value) => setVideoMode(value === 'under' ? 'under' : 'replace')}
          />
        ) : null}
        {picked.voice !== null && picked.music === null ? (
          <UIButton variant="secondary" onClick={() => openSection('music', { match: picked.voice ?? '' })}>
            {t('mix.music.generate')}
          </UIButton>
        ) : null}
        <UIButton disabled={!ready || create.isPending} onClick={() => create.mutate()}>
          {t('mix.create')}
        </UIButton>
      </UICard>
    </UIStack>
  );
}

import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { openUrl } from '@tauri-apps/plugin-opener';
import { useApi } from '@/shared/api/context';
import { UIButton } from '@/shared/components/atoms/UIButton';
import { UILink } from '@/shared/components/atoms/UILink';
import { UIStack } from '@/shared/components/atoms/UIStack';
import { UIText } from '@/shared/components/atoms/UIText';
import { UIField } from '@/shared/components/molecules/UIField';
import { t } from '@/shared/i18n/t';

/** Modelo restringido de pyannote: hay que aceptar sus condiciones con la cuenta del usuario (spec 034). */
export const HF_MODEL_URL = 'https://huggingface.co/pyannote/speaker-diarization-community-1';
const TOKEN_PATH = '/credentials/huggingface';

type Props = { configured: boolean };

/** Campo del token de Hugging Face de un motor restringido: se guarda sin mostrarlo y se puede quitar. */
export function HfTokenField({ configured }: Props): React.JSX.Element {
  const api = useApi();
  const queryClient = useQueryClient();
  const [draft, setDraft] = useState('');
  const refresh = () => queryClient.invalidateQueries({ queryKey: ['credentials', 'huggingface'] });
  const save = useMutation({
    mutationFn: () => api.put(TOKEN_PATH, { token: draft.trim() }),
    onSuccess: async () => {
      setDraft('');
      await refresh();
    },
  });
  const remove = useMutation({
    mutationFn: () => api.del(TOKEN_PATH),
    onSuccess: refresh,
  });

  return (
    <UIStack gap="sm">
      <UIText variant="caption">{t('engines.hf.help')}</UIText>
      <UILink
        href={HF_MODEL_URL}
        variant="inline"
        onClick={(event) => {
          event.preventDefault();
          void openUrl(HF_MODEL_URL);
        }}
      >
        {t('engines.hf.accept')}
      </UILink>
      {configured ? (
        <UIStack direction="row" gap="sm" align="center" className="flex-wrap">
          <UIText variant="body">{t('engines.hf.saved')}</UIText>
          <UIButton variant="secondary" disabled={remove.isPending} onClick={() => remove.mutate()}>
            {t('engines.hf.remove')}
          </UIButton>
        </UIStack>
      ) : (
        <UIStack direction="row" gap="sm" align="end" className="flex-wrap">
          <UIField
            label={t('engines.hf.token')}
            type="password"
            autoComplete="off"
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
          />
          <UIButton disabled={!draft.trim() || save.isPending} onClick={() => save.mutate()}>
            {t('engines.hf.save')}
          </UIButton>
        </UIStack>
      )}
    </UIStack>
  );
}

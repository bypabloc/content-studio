import { useMutation, useQueryClient } from '@tanstack/react-query';

import { useApi } from '@/shared/api/context';
import { UIButton } from '@/shared/components/atoms/UIButton';
import { UIStack } from '@/shared/components/atoms/UIStack';
import { UIText } from '@/shared/components/atoms/UIText';
import { UIDescriptionList } from '@/shared/components/molecules/UIDescriptionList';
import { toast } from '@/shared/components/molecules/UIToast';
import { t } from '@/shared/i18n/t';
import { openSection } from '@/shared/navigation/hash';

import { repeatSection } from './query';
import type { ItemDetailData } from './types';

/** Un valor de `params` legible: texto tal cual, el resto en JSON. */
function readable(value: unknown): string {
  return typeof value === 'string' ? value : JSON.stringify(value);
}

interface Props {
  detail: ItemDetailData;
  onOpen: (id: number) => void;
  onClose: () => void;
}

/** El origen (D-4): los parámetros del trabajo, «Repetir», «Editar y repetir», las otras salidas y las tomas. */
export function ItemOrigin({ detail, onOpen, onClose }: Props): React.JSX.Element | null {
  const api = useApi();
  const queryClient = useQueryClient();
  const repeat = useMutation({
    mutationFn: () => api.post(`/library/${detail.item.id}/repeat`),
    onSuccess: () => {
      toast.success(t('library.repeat.queued'));
      void queryClient.invalidateQueries({ queryKey: ['jobs'] });
    },
    onError: (error: Error) => toast.error(error.message),
  });
  const { job } = detail;
  if (job === null) return <UIText variant="caption">{t('library.origin.none')}</UIText>;
  const section = repeatSection(detail.item.kind);
  const params = Object.entries(job.params).map(([key, value]) => ({ icon: 'settings' as const, term: key, detail: readable(value) }));
  return (
    <UIStack gap="md" role="group" aria-label={t('library.origin')}>
      <UIText variant="subtitle">{t('library.origin')}</UIText>
      <UIText variant="caption">
        {t('library.origin.job_line', { id: job.id, kind: job.kind, seconds: job.elapsed === null ? '—' : Math.round(job.elapsed) })}
      </UIText>
      {params.length > 0 ? <UIDescriptionList items={params} /> : null}
      <UIStack direction="row" gap="sm">
        <UIButton variant="secondary" icon="retry" loading={repeat.isPending} onClick={() => repeat.mutate()}>
          {t('library.repeat')}
        </UIButton>
        {section ? (
          <UIButton
            variant="secondary"
            icon="pencil"
            onClick={() => {
              onClose();
              openSection(section, { from_job: String(job.id) });
            }}
          >
            {t('library.edit_repeat')}
          </UIButton>
        ) : null}
      </UIStack>
      {detail.outputs.length > 0 ? <UIText variant="caption">{t('library.outputs')}</UIText> : null}
      {detail.outputs.map((output) => (
        <UIButton key={output.id} variant="ghost" className="justify-start" onClick={() => onOpen(output.id)}>
          {output.path.split(/[\\/]/).pop()}
        </UIButton>
      ))}
      {detail.takes.length > 0 ? <UIText variant="caption">{t('library.takes')}</UIText> : null}
      {detail.takes.map((take) => (
        <UIButton key={take.id} variant="ghost" icon={take.starred ? 'star' : undefined} className="justify-start" onClick={() => onOpen(take.id)}>
          {take.path.split(/[\\/]/).pop()}
        </UIButton>
      ))}
    </UIStack>
  );
}

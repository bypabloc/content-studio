import { useQuery } from '@tanstack/react-query';

import { useApi } from '@/shared/api/context';
import type { Job } from '@/shared/api/events';
import { UIStack } from '@/shared/components/atoms/UIStack';
import { UIText } from '@/shared/components/atoms/UIText';
import { UIButton } from '@/shared/components/atoms/UIButton';
import { UIAlert } from '@/shared/components/molecules/UIAlert';
import { UIDescriptionList } from '@/shared/components/molecules/UIDescriptionList';
import { t } from '@/shared/i18n/t';

interface Props {
  id: number;
  onClose: () => void;
}

/** El detalle de un trabajo que llega por un enlace `job/<id>` (spec 031, AC-2). Si el id no existe, sale el error de la API. */
export function JobDetail({ id, onClose }: Props): React.JSX.Element {
  const api = useApi();
  const job = useQuery({ queryKey: ['job', id], queryFn: () => api.get<Job>(`/jobs/${id}`), retry: false });
  return (
    <UIStack className="space-y-3">
      <UIText variant="caption">{t('library.job.title')}</UIText>
      {job.isError ? <UIAlert>{job.error.message}</UIAlert> : null}
      {job.data ? (
        <UIDescriptionList
          items={[
            { icon: 'layers', term: t('library.job.kind'), detail: job.data.kind },
            { icon: 'server', term: t('library.job.status'), detail: job.data.status },
            { icon: 'library', term: t('library.job.output'), detail: job.data.output_dir ?? '-' },
          ]}
        />
      ) : null}
      <UIButton variant="secondary" onClick={onClose}>{t('media.dialog.close')}</UIButton>
    </UIStack>
  );
}

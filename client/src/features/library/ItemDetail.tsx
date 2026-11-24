import { useQuery } from '@tanstack/react-query';

import { useApi } from '@/shared/api/context';
import { UIMedia } from '@/shared/components/atoms/UIMedia';
import { UISkeleton } from '@/shared/components/atoms/UISkeleton';
import { UIStack } from '@/shared/components/atoms/UIStack';
import { UIDescriptionList } from '@/shared/components/molecules/UIDescriptionList';
import { UIDialog } from '@/shared/components/organisms/UIDialog';
import { t } from '@/shared/i18n/t';
import { Player } from '@/shared/media/Player';
import { useMediaPeaks } from '@/shared/media/useMediaInfo';

import { ItemActions } from './ItemActions';
import { ItemOrganize } from './ItemOrganize';
import { ItemOrigin } from './ItemOrigin';
import { PublishTab } from './PublishTab';
import { formatDate, formatDuration, formatSize, kindLabel } from './query';
import type { ItemDetailData, LibraryItem } from './types';

/** El reproductor del ítem: audio con su onda, video con los controles del sistema. */
function Preview({ item }: { item: LibraryItem }): React.JSX.Element | null {
  const api = useApi();
  const peaks = useMediaPeaks(item.media_type === 'audio' ? item.path : '');
  if (item.media_type === 'video') return <UIMedia kind="video" controls src={api.fileUrl(item.path)} label={item.name} className="w-full rounded-lg" />;
  if (item.media_type === 'audio' && peaks.data) return <Player src={api.fileUrl(item.path)} peaks={peaks.data.peaks} />;
  return null;
}

interface Props {
  id: number;
  onOpen: (id: number) => void;
  onClose: () => void;
}

/** El detalle (D-6): reproductor, metadatos, origen, etiquetas, proyectos y acciones, en un diálogo. */
export function ItemDetail({ id, onOpen, onClose }: Props): React.JSX.Element {
  const api = useApi();
  const detail = useQuery({ queryKey: ['library', 'item', id], queryFn: () => api.get<ItemDetailData>(`/library/${id}`) });
  const item = detail.data?.item;
  return (
    <UIDialog open onOpenChange={(open) => (open ? undefined : onClose())} title={item?.name ?? t('library.detail')} closeLabel={t('ui.dialog.close')}>
      {detail.data && item ? (
        <UIStack gap="lg">
          <Preview item={item} />
          <UIDescriptionList
            items={[
              { icon: 'layers', term: t('library.filter.kind'), detail: kindLabel(item.kind) },
              { icon: 'clock', term: t('library.filter.length'), detail: formatDuration(item.duration) },
              { icon: 'hard-drive', term: t('library.size'), detail: formatSize(item.size) },
              { icon: 'calendar', term: t('library.filter.date'), detail: formatDate(item.mtime) },
              { icon: 'open-folder', term: t('library.path'), detail: item.path },
            ]}
          />
          <ItemOrigin detail={detail.data} onOpen={onOpen} onClose={onClose} />
          <ItemOrganize item={item} />
          <ItemActions item={item} hasJob={detail.data.job !== null} onDone={onClose} />
          {item.media_type === 'video' || item.media_type === 'audio' ? <PublishTab item={item} /> : null}
        </UIStack>
      ) : (
        <UISkeleton className="h-64 w-full rounded-xl" />
      )}
    </UIDialog>
  );
}

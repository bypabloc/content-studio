import { useApi } from '@/shared/api/context';
import { UIBadge } from '@/shared/components/atoms/UIBadge';
import { UIButton } from '@/shared/components/atoms/UIButton';
import { UIGrid } from '@/shared/components/atoms/UIGrid';
import { UIIcon } from '@/shared/components/atoms/UIIcon';
import { UIImage } from '@/shared/components/atoms/UIImage';
import { UIStack } from '@/shared/components/atoms/UIStack';
import { UIText } from '@/shared/components/atoms/UIText';
import { t } from '@/shared/i18n/t';

import { AudioThumb } from './AudioThumb';
import { formatDuration, kindLabel } from './query';
import type { LibraryItem } from './types';

/** La miniatura de la tarjeta: cuadro del video o la imagen, onda del audio o un ícono para los subtítulos. */
function Thumb({ item }: { item: LibraryItem }): React.JSX.Element {
  const api = useApi();
  if (item.media_type === 'audio') return <AudioThumb path={item.path} label={t('library.thumb', { name: item.name })} />;
  if (item.media_type === 'subtitle') return <UIIcon name="subtitles" className="size-16" />;
  return (
    <UIImage
      src={api.queryUrl(`/library/thumb/${item.id}`, {})}
      alt={t('library.thumb', { name: item.name })}
      width={240}
      height={135}
      loading="lazy"
      className="aspect-video w-full rounded-lg object-cover"
    />
  );
}

/** La grilla (D-6): tarjetas con miniatura, nombre, duración, tipo, ★ y etiquetas. */
export function LibraryGrid({ items, onOpen }: { items: LibraryItem[]; onOpen: (id: number) => void }): React.JSX.Element {
  return (
    <UIGrid columns={4} role="list" aria-label={t('library.results')}>
      {items.map((item) => (
        <UIStack key={item.id} role="listitem" gap="sm">
          <UIButton variant="ghost" className="h-auto flex-col items-stretch p-2" aria-label={t('library.open', { name: item.name })} onClick={() => onOpen(item.id)}>
            <Thumb item={item} />
            <UIText variant="body" className="truncate">{item.name}</UIText>
          </UIButton>
          <UIStack direction="row" gap="sm" className="flex-wrap">
            <UIBadge>{kindLabel(item.kind)}</UIBadge>
            <UIBadge icon="clock">{formatDuration(item.duration)}</UIBadge>
            {item.starred ? <UIBadge icon="star">{t('library.starred')}</UIBadge> : null}
            {item.missing ? <UIBadge tone="danger">{t('library.missing')}</UIBadge> : null}
            {item.tags.map((tag) => (
              <UIBadge key={tag} icon="tag">{tag}</UIBadge>
            ))}
          </UIStack>
        </UIStack>
      ))}
    </UIGrid>
  );
}

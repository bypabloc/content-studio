import { UIButton } from '@/shared/components/atoms/UIButton';
import { UICheckbox } from '@/shared/components/atoms/UICheckbox';
import { UIStack } from '@/shared/components/atoms/UIStack';
import { UIText } from '@/shared/components/atoms/UIText';
import { UIVirtualList } from '@/shared/components/molecules/UIVirtualList';
import { t } from '@/shared/i18n/t';

import { formatDate, formatDuration, formatSize, kindLabel } from './query';
import type { LibraryItem } from './types';

const ROW_HEIGHT = 44;
const HEIGHT = 560;

interface Props {
  items: LibraryItem[];
  onOpen: (id: number) => void;
  selected: number[];
  onSelect: (selected: number[]) => void;
}

/** La lista densa (D-6): nombre, tipo, duración, tamaño, fecha y origen, con selección múltiple; solo las filas visibles van al DOM (AC-9). */
export function LibraryList({ items, onOpen, selected, onSelect }: Props): React.JSX.Element {
  const toggle = (id: number, checked: boolean) => onSelect(checked ? [...selected, id] : selected.filter((other) => other !== id));
  return (
    <UIVirtualList
      label={t('library.results')}
      count={items.length}
      rowHeight={ROW_HEIGHT}
      height={HEIGHT}
      renderRow={(index) => {
        const item = items[index];
        return (
          <UIStack direction="row" gap="md" align="center" className="h-full border-b border-border px-2">
            <UICheckbox label={t('library.select', { name: item.name })} checked={selected.includes(item.id)} onChange={(checked) => toggle(item.id, checked)} />
            <UIButton variant="ghost" className="min-w-0 flex-1 justify-start truncate" onClick={() => onOpen(item.id)}>
              {item.name}
            </UIButton>
            <UIText variant="caption" className="w-28">{kindLabel(item.kind)}</UIText>
            <UIText variant="caption" className="w-16 text-right tabular-nums">{formatDuration(item.duration)}</UIText>
            <UIText variant="caption" className="w-20 text-right tabular-nums">{formatSize(item.size)}</UIText>
            <UIText variant="caption" className="w-24 text-right tabular-nums">{formatDate(item.mtime)}</UIText>
            <UIText variant="caption" className="w-24">{item.origin === 'job' ? t('library.origin.job') : t('library.origin.watched')}</UIText>
          </UIStack>
        );
      }}
    />
  );
}

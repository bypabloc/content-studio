import { UIStack } from '@/shared/components/atoms/UIStack';
import { UISwitch } from '@/shared/components/atoms/UISwitch';
import { UIIconButton } from '@/shared/components/molecules/UIIconButton';
import { UISearchField } from '@/shared/components/molecules/UISearchField';
import { UISelect } from '@/shared/components/molecules/UISelect';
import { t } from '@/shared/i18n/t';

import { kindLabel } from './query';
import type { Filters, TagCount } from './types';

export const KINDS = ['narration', 'music', 'clean', 'subtitles', 'convert', 'normalize', 'mix', 'editor', 'trim', 'concat', 'split', 'watched'];
const ANY = 'any'; // el selector no admite un valor vacío: «cualquiera» es su propia opción

interface Props {
  filters: Filters;
  onChange: (filters: Filters) => void;
  tags: TagCount[];
  view: 'grid' | 'list';
  onView: (view: 'grid' | 'list') => void;
  scanning: boolean;
  onRefresh: () => void;
}

/** La barra de la Biblioteca (D-6): búsqueda, «Buscar en el contenido», filtros, orden, vista y «Actualizar». */
export function LibraryToolbar({ filters, onChange, tags, view, onView, scanning, onRefresh }: Props): React.JSX.Element {
  const set = (change: Partial<Filters>) => onChange({ ...filters, ...change });
  const pick = (value: string) => (value === ANY ? '' : value);
  return (
    <UIStack gap="sm">
      <UIStack direction="row" gap="sm" align="end" className="flex-wrap">
        <UISearchField label={t('library.search')} value={filters.q} onChange={(q) => set({ q })} />
        <UISwitch label={t('library.search.content')} checked={filters.content} onChange={(content) => set({ content })} />
        <UIIconButton icon="layout-grid" label={t('library.view.grid')} pressed={view === 'grid'} onClick={() => onView('grid')} />
        <UIIconButton icon="list" label={t('library.view.list')} pressed={view === 'list'} onClick={() => onView('list')} />
        <UIIconButton icon="refresh-cw" label={t('library.refresh')} loading={scanning} onClick={onRefresh} />
      </UIStack>
      <UIStack direction="row" gap="sm" className="flex-wrap">
        <UISelect
          label={t('library.filter.kind')}
          value={filters.kind || ANY}
          options={[{ value: ANY, label: t('library.filter.any') }, ...KINDS.map((kind) => ({ value: kind, label: kindLabel(kind) }))]}
          onChange={(value) => set({ kind: pick(value) })}
        />
        <UISelect
          label={t('library.filter.media')}
          value={filters.mediaType || ANY}
          options={[
            { value: ANY, label: t('library.filter.any') },
            { value: 'audio', label: t('library.media.audio') },
            { value: 'video', label: t('library.media.video') },
            { value: 'subtitle', label: t('library.media.subtitle') },
            { value: 'other', label: t('library.media.other') },
          ]}
          onChange={(value) => set({ mediaType: pick(value) })}
        />
        <UISelect
          label={t('library.filter.date')}
          value={filters.since || ANY}
          options={[
            { value: ANY, label: t('library.filter.any') },
            { value: 'today', label: t('library.date.today') },
            { value: 'week', label: t('library.date.week') },
            { value: 'month', label: t('library.date.month') },
          ]}
          onChange={(value) => set({ since: pick(value) })}
        />
        <UISelect
          label={t('library.filter.length')}
          value={filters.length || ANY}
          options={[
            { value: ANY, label: t('library.filter.any') },
            { value: 'short', label: t('library.length.short') },
            { value: 'medium', label: t('library.length.medium') },
            { value: 'long', label: t('library.length.long') },
          ]}
          onChange={(value) => set({ length: pick(value) })}
        />
        <UISelect
          label={t('library.filter.tag')}
          value={filters.tag || ANY}
          options={[{ value: ANY, label: t('library.filter.any') }, ...tags.map((tag) => ({ value: tag.name, label: tag.name }))]}
          onChange={(value) => set({ tag: pick(value) })}
        />
        <UISelect
          label={t('library.sort')}
          value={filters.sort}
          options={[
            { value: 'date', label: t('library.sort.date') },
            { value: 'name', label: t('library.sort.name') },
            { value: 'size', label: t('library.sort.size') },
            { value: 'duration', label: t('library.sort.duration') },
          ]}
          onChange={(sort) => set({ sort })}
        />
        <UISwitch label={t('library.filter.starred')} checked={filters.starred} onChange={(starred) => set({ starred })} />
      </UIStack>
    </UIStack>
  );
}

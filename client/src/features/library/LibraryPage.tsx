import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';

import { useApi } from '@/shared/api/context';
import { UIStack } from '@/shared/components/atoms/UIStack';
import { UIText } from '@/shared/components/atoms/UIText';
import { UIEmpty } from '@/shared/components/molecules/UIEmpty';
import { UIPagination } from '@/shared/components/molecules/UIPagination';
import { toast } from '@/shared/components/molecules/UIToast';
import { UIConfirmDialog } from '@/shared/components/organisms/UIConfirmDialog';
import { useSetting } from '@/shared/hooks/useSetting';
import { t } from '@/shared/i18n/t';

import { FolderSidebar } from './FolderSidebar';
import { ItemDetail } from './ItemDetail';
import { LibraryGrid } from './LibraryGrid';
import { LibraryList } from './LibraryList';
import { LibraryToolbar } from './LibraryToolbar';
import { EMPTY_FILTERS } from './query';
import { StorageView } from './StorageView';
import type { Filters, Scope } from './types';
import { useAutoScan, useLibraryItems, useScan, useTags } from './useLibrary';

const PAGE_SIZE = 200;

/**
 * La sección Biblioteca (spec 020, D-6): todo lo generado y las carpetas vigiladas, con búsqueda, filtros, etiquetas,
 * proyectos, grilla o lista, el detalle con reproductor y acciones, y el resumen del espacio. Al abrir escanea las
 * carpetas si el último escaneo tiene más de 5 minutos.
 */
export function LibraryPage(): React.JSX.Element {
  const api = useApi();
  const queryClient = useQueryClient();
  const [filters, setFilters] = useState<Filters>(EMPTY_FILTERS);
  const [scope, setScope] = useState<Scope>({ type: 'all' });
  const [page, setPage] = useState(1);
  const [view, setView] = useSetting<'grid' | 'list'>('library.view', 'grid');
  const [openId, setOpenId] = useState<number | null>(null);
  const [selected, setSelected] = useState<number[]>([]);
  const scan = useScan();
  useAutoScan(scan.refresh);
  const items = useLibraryItems(filters, scope, page);
  const tags = useTags();
  const trash = useMutation({
    mutationFn: () => api.post<{ removed: number }>('/library/trash', { items: selected }),
    onSuccess: (result) => {
      toast.success(t('library.trash.done', { count: result.removed }));
      setSelected([]);
      void queryClient.invalidateQueries({ queryKey: ['library'] });
    },
    onError: (error: Error) => toast.error(error.message),
  });
  const list = items.data?.items ?? [];
  const total = items.data?.total ?? 0;

  return (
    <UIStack gap="lg" className="lg:flex-row lg:items-start">
      <FolderSidebar
        scope={scope}
        onAdded={scan.refresh}
        onScope={(next) => {
          setScope(next);
          setPage(1);
        }}
      />
      <UIStack gap="md" className="min-w-0 lg:flex-1">
        {scope.type === 'storage' ? (
          <StorageView />
        ) : (
          <>
            <LibraryToolbar
              filters={filters}
              onChange={(next) => {
                setFilters(next);
                setPage(1);
              }}
              tags={tags.data ?? []}
              view={view}
              onView={setView}
              scanning={scan.scanning}
              onRefresh={scan.refresh}
            />
            <UIText variant="caption" role="status">{t('library.count', { count: total })}</UIText>
            {items.isSuccess && list.length === 0 ? (
              <UIEmpty icon="library" title={t('library.empty')} description={t('library.empty.hint')} />
            ) : null}
            {view === 'grid' ? (
              <LibraryGrid items={list} onOpen={setOpenId} />
            ) : (
              <LibraryList items={list} onOpen={setOpenId} selected={selected} onSelect={setSelected} />
            )}
            {view === 'list' && selected.length > 0 ? (
              <UIConfirmDialog
                triggerLabel={t('library.trash')}
                triggerIcon="remove"
                title={t('library.trash')}
                description={t('library.trash.confirm_list', { count: selected.length })}
                confirmLabel={t('library.trash')}
                cancelLabel={t('action.cancel')}
                destructive
                pending={trash.isPending}
                onConfirm={() => trash.mutate()}
              />
            ) : null}
            {total > PAGE_SIZE ? (
              <UIPagination
                total={total}
                limit={PAGE_SIZE}
                offset={(page - 1) * PAGE_SIZE}
                onChange={(offset) => setPage(offset / PAGE_SIZE + 1)}
                summary={t('library.count', { count: total })}
                labels={{ nav: t('library.pages'), previous: t('library.pages.previous'), next: t('library.pages.next') }}
              />
            ) : null}
          </>
        )}
      </UIStack>
      {openId !== null ? <ItemDetail id={openId} onOpen={setOpenId} onClose={() => setOpenId(null)} /> : null}
    </UIStack>
  );
}

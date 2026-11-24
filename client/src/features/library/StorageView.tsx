import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';

import { useApi } from '@/shared/api/context';
import { UICard } from '@/shared/components/atoms/UICard';
import { UICheckbox } from '@/shared/components/atoms/UICheckbox';
import { UISkeleton } from '@/shared/components/atoms/UISkeleton';
import { UIStack } from '@/shared/components/atoms/UIStack';
import { UIText } from '@/shared/components/atoms/UIText';
import { toast } from '@/shared/components/molecules/UIToast';
import { UIChart } from '@/shared/components/organisms/UIChart';
import { UIConfirmDialog } from '@/shared/components/organisms/UIConfirmDialog';
import { t } from '@/shared/i18n/t';

import { formatSize, kindLabel } from './query';
import type { LibraryItem, StorageData } from './types';

/** Una lista con selección múltiple y «Mandar a la papelera» con una sola confirmación (cantidad y tamaño). */
function TrashList({ title, items }: { title: string; items: LibraryItem[] }): React.JSX.Element {
  const api = useApi();
  const queryClient = useQueryClient();
  const [selected, setSelected] = useState<number[]>([]);
  const chosen = items.filter((item) => selected.includes(item.id));
  const size = chosen.reduce((total, item) => total + item.size, 0);
  const trash = useMutation({
    mutationFn: () => api.post<{ removed: number }>('/library/trash', { items: selected }),
    onSuccess: (result) => {
      toast.success(t('library.trash.done', { count: result.removed }));
      setSelected([]);
      void queryClient.invalidateQueries({ queryKey: ['library'] });
    },
    onError: (error: Error) => toast.error(error.message),
  });
  return (
    <UICard aria-label={title}>
      <UIStack gap="sm">
        <UIText variant="subtitle">{title}</UIText>
        {items.length === 0 ? <UIText variant="caption">{t('library.storage.empty')}</UIText> : null}
        {items.map((item) => (
          <UICheckbox
            key={item.id}
            label={t('library.storage.row', { name: item.path.split(/[\\/]/).pop() ?? item.path, size: formatSize(item.size) })}
            checked={selected.includes(item.id)}
            onChange={(checked) => setSelected(checked ? [...selected, item.id] : selected.filter((id) => id !== item.id))}
          />
        ))}
        {chosen.length > 0 ? (
          <UIConfirmDialog
            triggerLabel={t('library.trash')}
            triggerIcon="remove"
            title={t('library.trash')}
            description={t('library.trash.confirm', { count: chosen.length, size: formatSize(size) })}
            confirmLabel={t('library.trash')}
            cancelLabel={t('action.cancel')}
            destructive
            pending={trash.isPending}
            onConfirm={() => trash.mutate()}
          />
        ) : null}
      </UIStack>
    </UICard>
  );
}

/** «Espacio» (D-5): barras por tipo, lo más pesado y las tomas no elegidas. Nunca borra nada sin confirmar. */
export function StorageView(): React.JSX.Element {
  const api = useApi();
  const storage = useQuery({ queryKey: ['library', 'storage'], queryFn: () => api.get<StorageData>('/library/storage') });
  if (!storage.data) return <UISkeleton className="h-64 w-full rounded-xl" />;
  const data = storage.data;
  return (
    <UIStack gap="lg">
      <UIText variant="body">
        {t('library.storage.total', { size: formatSize(data.outputs.size), path: data.outputs.path })}
      </UIText>
      {data.folders.map((folder) => (
        <UIText key={folder.id} variant="caption">
          {t('library.storage.folder', { name: folder.name ?? folder.path, size: formatSize(folder.size) })}
        </UIText>
      ))}
      <UIChart
        kind="bar"
        ariaLabel={t('library.storage.by_kind')}
        data={data.by_kind.map((row) => ({ kind: kindLabel(row.kind), size: row.size }))}
        series={[{ key: 'size', label: t('library.size'), color: 1 }]}
        xKey="kind"
        formatY={formatSize}
        height={240}
      />
      <TrashList title={t('library.storage.heaviest')} items={data.heaviest} />
      <TrashList title={t('library.storage.unchosen')} items={data.unchosen} />
    </UIStack>
  );
}

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useApi } from '@/shared/api/context';
import type { components } from '@/shared/api/schema';
import { UIButton } from '@/shared/components/atoms/UIButton';
import { UICard } from '@/shared/components/atoms/UICard';
import { UIStack } from '@/shared/components/atoms/UIStack';
import { UIText } from '@/shared/components/atoms/UIText';
import { t } from '@/shared/i18n/t';

export type StorageInfo = components['schemas']['StoragePaths'];

function formatBytes(bytes: number): string {
  if (bytes >= 1_000_000_000) return `${Number((bytes / 1_000_000_000).toFixed(1))} GB`;
  if (bytes >= 1_000_000) return `${Number((bytes / 1_000_000).toFixed(1))} MB`;
  if (bytes >= 1_000) return `${Number((bytes / 1_000).toFixed(1))} KB`;
  return `${bytes} B`;
}

function estimateMove(bytes: number): string {
  const minutes = Math.max(1, Math.ceil(bytes / (50_000_000 * 60)));
  if (minutes < 60) return t('storage.estimate.minutes', { minutes });
  return t('storage.estimate.hours', { hours: Math.floor(minutes / 60), minutes: minutes % 60 });
}

export function StorageSettings(): React.JSX.Element {
  const api = useApi();
  const queryClient = useQueryClient();
  const storage = useQuery({ queryKey: ['storage'], queryFn: () => api.get<StorageInfo>('/storage') });
  const move = useMutation({
    mutationFn: (body: { target: 'engines' | 'outputs'; to: string }) => api.post('/storage/move', body),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['storage'] }),
        queryClient.invalidateQueries({ queryKey: ['jobs'] }),
      ]);
    },
  });

  async function choose(target: 'engines' | 'outputs', current: string, used: number): Promise<void> {
    const { open } = await import('@tauri-apps/plugin-dialog');
    const destination = await open({ directory: true, multiple: false, title: t('storage.choose_folder') });
    if (typeof destination !== 'string' || destination === current) return;
    if (!window.confirm(t('storage.confirm_move', {
      folder: t(`storage.${target}`),
      used: formatBytes(used),
      path: destination,
      estimate: estimateMove(used),
    }))) return;
    move.mutate({ target, to: destination });
  }

  if (storage.isPending) return <UIText variant="caption">{t('storage.loading')}</UIText>;
  if (storage.isError) return <UIText variant="caption">{t('storage.load_error')}</UIText>;

  const value = storage.data;
  const folders = [
    { key: 'engines' as const, path: value.engines, used: value.engines_used_bytes, free: value.engines_free_bytes },
    { key: 'outputs' as const, path: value.outputs, used: value.outputs_used_bytes, free: value.outputs_free_bytes },
  ];

  return (
    <UIStack gap="md" className="max-w-3xl">
      <UIText variant="heading">{t('storage.title')}</UIText>
      {folders.map(({ key, path, used, free }) => (
        <UICard key={key} aria-label={t(`storage.${key}`)}>
          <UIStack gap="sm">
            <UIText variant="subtitle">{t(`storage.${key}`)}</UIText>
            <UIText variant="body">{path}</UIText>
            <UIStack direction="row" gap="md" className="flex-wrap">
              <UIText variant="caption">{t('storage.used', { size: formatBytes(used) })}</UIText>
              <UIText variant="caption">{t('storage.free', { size: formatBytes(free) })}</UIText>
            </UIStack>
            <UIButton
              variant="secondary"
              disabled={move.isPending}
              onClick={() => void choose(key, path, used)}
            >
              {t('storage.change_folder', { folder: t(`storage.${key}`) })}
            </UIButton>
          </UIStack>
        </UICard>
      ))}
    </UIStack>
  );
}

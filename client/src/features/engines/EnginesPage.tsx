import { useEffect } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useApi } from '@/shared/api/context';
import type { components } from '@/shared/api/schema';
import { UIStack } from '@/shared/components/atoms/UIStack';
import { UIText } from '@/shared/components/atoms/UIText';
import { t } from '@/shared/i18n/t';
import { EngineCard, type EngineAction } from './EngineCard';

type EngineInfo = components['schemas']['EngineInfo'];
type GpuInfo = components['schemas']['GpuInfo'];
type SystemInfo = { ffmpeg: { path: string; version: string } | null; git: { path: string; version: string } | null; gpu: GpuInfo | null };

const GROUPS = [
  ['narration', 'engines.group.narration'],
  ['music', 'engines.group.music'],
  ['transcription', 'engines.group.transcription'],
] as const;

function requestedEngine(): string | null {
  return new URLSearchParams(window.location.hash.split('?')[1] ?? '').get('engine');
}

function actionPath(action: EngineAction): string {
  const engine = encodeURIComponent(action.engine);
  if (action.type === 'repair') return `/engines/${engine}/install?repair=true`;
  if (action.type === 'uninstall') return `/engines/${engine}/uninstall${action.force ? '?force=true' : ''}`;
  return `/engines/${engine}/${action.type}`;
}

export function EnginesPage(): React.JSX.Element {
  const api = useApi();
  const queryClient = useQueryClient();
  const enginesQuery = useQuery({ queryKey: ['engines'], queryFn: () => api.get<EngineInfo[]>('/engines') });
  const systemQuery = useQuery({ queryKey: ['system'], queryFn: () => api.get<SystemInfo>('/system') });
  const mutation = useMutation({
    mutationFn: (action: EngineAction) => api.post(actionPath(action)),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['engines'] }),
        queryClient.invalidateQueries({ queryKey: ['catalog', 'narration'] }),
        queryClient.invalidateQueries({ queryKey: ['jobs'] }),
      ]);
    },
  });
  const selectedEngine = requestedEngine();

  useEffect(() => {
    if (!selectedEngine || !enginesQuery.data?.some((engine) => engine.engine === selectedEngine)) return;
    document.getElementById(`engine-card-${selectedEngine}`)?.scrollIntoView?.({ block: 'center' });
  }, [selectedEngine, enginesQuery.data]);

  if (enginesQuery.isPending || systemQuery.isPending) return <UIText variant="caption">{t('engines.loading')}</UIText>;
  if (enginesQuery.isError || systemQuery.isError) return <UIText variant="caption">{t('engines.load_error')}</UIText>;

  const engines = enginesQuery.data ?? [];
  return (
    <UIStack gap="lg">
      <UIText variant="title">{t('engines.title')}</UIText>
      {GROUPS.map(([family, key]) => {
        const groupEngines = engines.filter((engine) => engine.family === family);
        if (!groupEngines.length) return null;
        return (
          <UIStack key={family} gap="md">
            <UIText variant="subtitle">{t(key)}</UIText>
            {groupEngines.map((engine) => (
              <EngineCard
                key={engine.engine}
                engine={engine}
                gpu={systemQuery.data.gpu}
                busy={mutation.isPending}
                highlighted={engine.engine === selectedEngine}
                onAction={(action) => mutation.mutate(action)}
              />
            ))}
          </UIStack>
        );
      })}
    </UIStack>
  );
}

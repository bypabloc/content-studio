import { lazy, Suspense } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useApi } from '@/shared/api/context';
import type { components } from '@/shared/api/schema';
import { UIButton } from '@/shared/components/atoms/UIButton';
import { UIStack } from '@/shared/components/atoms/UIStack';
import { UIText } from '@/shared/components/atoms/UIText';
import { useSetting } from '@/shared/hooks/useSetting';
import { t } from '@/shared/i18n/t';

const WelcomeWizard = lazy(() => import('./WelcomeWizard').then((module) => ({ default: module.WelcomeWizard })));

type EngineInfo = components['schemas']['EngineInfo'];
type GpuInfo = components['schemas']['GpuInfo'];
type SystemInfo = { ffmpeg: { path: string; version: string } | null; git: { path: string; version: string } | null; gpu: GpuInfo | null };
type StorageInfo = components['schemas']['StoragePaths'];

export function WelcomeGate(): React.JSX.Element | null {
  const api = useApi();
  const [done, setDone] = useSetting<boolean>('welcome.done', false);
  const engines = useQuery({ queryKey: ['engines'], queryFn: () => api.get<EngineInfo[]>('/engines') });
  const system = useQuery({ queryKey: ['system'], queryFn: () => api.get<SystemInfo>('/system') });
  const storage = useQuery({ queryKey: ['storage'], queryFn: () => api.get<StorageInfo>('/storage') });

  if (!system.data || !storage.data || !engines.data) return null;
  const hasEngine = engines.data.some((engine) => ['installed', 'external'].includes(engine.status));
  const firstRun = !done && !hasEngine;
  return (
    <>
      {system.data.ffmpeg ? null : (
        <UIStack direction="row" align="center" gap="sm" role="status" className="rounded-xl border border-input bg-card p-3">
          <UIText variant="body">{t('system.ffmpeg.missing')}</UIText>
          <UIButton variant="secondary" onClick={() => void api.post('/system/tools/ffmpeg/install')}>
            {t('system.ffmpeg.install')}
          </UIButton>
        </UIStack>
      )}
      {firstRun ? (
        <Suspense fallback={null}>
          <WelcomeWizard
            open
            system={system.data}
            storage={storage.data}
            engines={engines.data}
            onComplete={() => setDone(true)}
          />
        </Suspense>
      ) : null}
    </>
  );
}

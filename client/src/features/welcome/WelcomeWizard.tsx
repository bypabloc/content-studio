import { useState } from 'react';
import { open } from '@tauri-apps/plugin-dialog';
import type { components } from '@/shared/api/schema';
import { useApi } from '@/shared/api/context';
import { UIBadge } from '@/shared/components/atoms/UIBadge';
import { UIButton } from '@/shared/components/atoms/UIButton';
import { UICheckbox } from '@/shared/components/atoms/UICheckbox';
import { UIProgress } from '@/shared/components/atoms/UIProgress';
import { UIStack } from '@/shared/components/atoms/UIStack';
import { UIText } from '@/shared/components/atoms/UIText';
import { UIDialog } from '@/shared/components/organisms/UIDialog';
import { t } from '@/shared/i18n/t';

type EngineInfo = components['schemas']['EngineInfo'];
type GpuInfo = components['schemas']['GpuInfo'];
type SystemInfo = { ffmpeg: { path: string; version: string } | null; git: { path: string; version: string } | null; gpu: GpuInfo | null };
type StorageInfo = components['schemas']['StoragePaths'];
type Props = { open: boolean; system: SystemInfo; storage: StorageInfo; engines?: EngineInfo[]; onComplete: () => void };

const RECOMMENDED = ['voxcpm2', 'acestep', 'faster-whisper'];

function formatBytes(bytes: number): string {
  if (bytes >= 1_000_000_000) return `${Number((bytes / 1_000_000_000).toFixed(1))} GB`;
  if (bytes >= 1_000_000) return `${Number((bytes / 1_000_000).toFixed(1))} MB`;
  return `${bytes} B`;
}

function estimateMove(bytes: number): string {
  const minutes = Math.max(1, Math.ceil(bytes / (50_000_000 * 60)));
  if (minutes < 60) return t('storage.estimate.minutes', { minutes });
  return t('storage.estimate.hours', { hours: Math.floor(minutes / 60), minutes: minutes % 60 });
}

export function WelcomeWizard({ open: visible, system, storage, engines = [], onComplete }: Props): React.JSX.Element | null {
  const api = useApi();
  const [step, setStep] = useState(1);
  const [selected, setSelected] = useState<string[]>(() => RECOMMENDED.filter((id) => engines.some((engine) => engine.engine === id)));
  const [error, setError] = useState(false);
  const [queuedFolders, setQueuedFolders] = useState<Partial<Record<'engines' | 'outputs', string>>>({});

  if (!visible) return null;

  async function installTool(name: 'ffmpeg' | 'git'): Promise<void> {
    await api.post(`/system/tools/${name}/install`);
  }

  async function chooseFolder(target: 'engines' | 'outputs', current: string, used: number): Promise<void> {
    const destination = await open({ directory: true, multiple: false, title: t('storage.choose_folder') });
    if (typeof destination !== 'string' || destination === current) return;
    if (window.confirm(t('storage.confirm_move', {
      folder: t(`storage.${target}`),
      used: formatBytes(used),
      path: destination,
      estimate: estimateMove(used),
    }))) {
      await api.post('/storage/move', { target, to: destination });
      setQueuedFolders((previous) => ({ ...previous, [target]: destination }));
    }
  }

  async function finish(): Promise<void> {
    setError(false);
    try {
      for (const engine of selected) await api.post(`/engines/${encodeURIComponent(engine)}/install`);
      onComplete();
      window.location.hash = '#/narration';
    } catch {
      setError(true);
    }
  }

  const recommended = engines.filter((engine) => RECOMMENDED.includes(engine.engine));
  const optional = engines.filter((engine) => !RECOMMENDED.includes(engine.engine));
  const selectedEngines = engines.filter((engine) => selected.includes(engine.engine));
  const totalSize = selectedEngines.reduce((total, engine) => total + engine.size_gb, 0);
  const toggle = (engine: string) => setSelected((current) => current.includes(engine) ? current.filter((id) => id !== engine) : [...current, engine]);

  return (
    <UIDialog
      open={visible}
      onOpenChange={() => undefined}
      title={t('welcome.title')}
      description={t('welcome.step', { current: step, total: 4 })}
      closeLabel={t('action.cancel')}
      footer={(
        <UIStack direction="row" justify="between">
          <UIButton variant="ghost" disabled={step === 1} onClick={() => setStep((current) => current - 1)}>
            {t('welcome.back')}
          </UIButton>
          {step < 4 ? (
            <UIButton onClick={() => setStep((current) => current + 1)}>{t('welcome.next')}</UIButton>
          ) : (
            <UIButton onClick={() => void finish()}>{t('welcome.install_continue')}</UIButton>
          )}
        </UIStack>
      )}
    >
      <UIStack gap="md">
        <UIProgress value={step / 4} label={t('welcome.progress')} />
        {step === 1 ? (
          <UIStack gap="md">
            <UIText variant="subtitle">{t('welcome.tools.title')}</UIText>
            {system.ffmpeg ? <UIBadge tone="accent">{t('welcome.tools.available', { tool: t('system.ffmpeg.name') })}</UIBadge> : (
              <UIButton variant="secondary" onClick={() => void installTool('ffmpeg')}>{t('welcome.tools.install_ffmpeg')}</UIButton>
            )}
            {system.git ? <UIBadge tone="accent">{t('welcome.tools.available', { tool: t('system.git.name') })}</UIBadge> : (
              <UIButton variant="secondary" onClick={() => void installTool('git')}>{t('welcome.tools.install_git')}</UIButton>
            )}
            <UIText variant="body">
              {system.gpu ? t('welcome.gpu.detected', { name: system.gpu.name, vram: system.gpu.vram_gb }) : t('welcome.gpu.none')}
            </UIText>
          </UIStack>
        ) : null}
        {step === 2 ? (
          <UIStack gap="md">
            <UIText variant="subtitle">{t('welcome.folders.title')}</UIText>
            <UIText variant="body">{t('storage.engines')}{': '}{queuedFolders.engines ?? storage.engines}</UIText>
            <UIButton variant="secondary" onClick={() => void chooseFolder('engines', storage.engines, storage.engines_used_bytes)}>
              {t('storage.change_folder', { folder: t('storage.engines') })}
            </UIButton>
            {queuedFolders.engines ? <UIText variant="caption">{t('welcome.folder_queued', { folder: t('storage.engines') })}</UIText> : null}
            <UIText variant="body">{t('storage.outputs')}{': '}{queuedFolders.outputs ?? storage.outputs}</UIText>
            <UIButton variant="secondary" onClick={() => void chooseFolder('outputs', storage.outputs, storage.outputs_used_bytes)}>
              {t('storage.change_folder', { folder: t('storage.outputs') })}
            </UIButton>
            {queuedFolders.outputs ? <UIText variant="caption">{t('welcome.folder_queued', { folder: t('storage.outputs') })}</UIText> : null}
          </UIStack>
        ) : null}
        {step === 3 ? (
          <UIStack gap="sm">
            <UIText variant="subtitle">{t('welcome.package.title')}</UIText>
            <UIText variant="caption">{t('welcome.package.total_size', { size: `${Number(totalSize.toFixed(1))} GB` })}</UIText>
            {recommended.map((engine) => (
              <UICheckbox
                key={engine.engine}
                label={engine.engine}
                description={t('engines.size', { size: `${engine.size_gb} GB` })}
                checked={selected.includes(engine.engine)}
                onChange={() => toggle(engine.engine)}
              />
            ))}
            {optional.length ? <UIText variant="heading">{t('welcome.package.optional')}</UIText> : null}
            {optional.map((engine) => (
              <UICheckbox
                key={engine.engine}
                label={engine.engine}
                description={t('engines.size', { size: `${engine.size_gb} GB` })}
                checked={selected.includes(engine.engine)}
                onChange={() => toggle(engine.engine)}
              />
            ))}
          </UIStack>
        ) : null}
        {step === 4 ? (
          <UIStack gap="md">
            <UIText variant="subtitle">{t('welcome.install.title')}</UIText>
            <UIText variant="body">{t('welcome.install.count', { count: selected.length })}</UIText>
            <UIText variant="body">{t('welcome.install.total', { size: `${Number(totalSize.toFixed(1))} GB` })}</UIText>
            {error ? <UIText variant="caption">{t('welcome.install.error')}</UIText> : null}
          </UIStack>
        ) : null}
      </UIStack>
    </UIDialog>
  );
}

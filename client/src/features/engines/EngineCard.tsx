import { useState } from 'react';
import type { components } from '@/shared/api/schema';
import { UIBadge } from '@/shared/components/atoms/UIBadge';
import { UIButton } from '@/shared/components/atoms/UIButton';
import { UICard } from '@/shared/components/atoms/UICard';
import { UIStack } from '@/shared/components/atoms/UIStack';
import { UIText } from '@/shared/components/atoms/UIText';
import { UIField } from '@/shared/components/molecules/UIField';
import { t } from '@/shared/i18n/t';

type EngineInfo = components['schemas']['EngineInfo'];
type GpuInfo = components['schemas']['GpuInfo'];
export type EngineAction = { type: 'install' | 'verify' | 'repair' | 'uninstall'; engine: string; force?: boolean };

type Props = {
  engine: EngineInfo;
  gpu: GpuInfo | null;
  onAction: (action: EngineAction) => void;
  busy?: boolean;
  highlighted?: boolean;
};

function bytesLabel(gb: number): string {
  return `${Number(gb.toFixed(1))} GB`;
}

function installedSize(engine: EngineInfo): string {
  if (engine.size_bytes <= 0) return bytesLabel(engine.size_gb);
  if (engine.size_bytes >= 1_000_000_000) return `${Number((engine.size_bytes / 1_000_000_000).toFixed(1))} GB`;
  if (engine.size_bytes >= 1_000_000) return `${Number((engine.size_bytes / 1_000_000).toFixed(1))} MB`;
  if (engine.size_bytes >= 1_000) return `${Number((engine.size_bytes / 1_000).toFixed(1))} KB`;
  return `${engine.size_bytes} B`;
}

function vramLabel(required: number, gpu: GpuInfo | null): string {
  if (!gpu) return t('engines.vram.no_gpu');
  if (gpu.vram_gb < required) return t('engines.vram.no_fit');
  if (gpu.vram_gb < required * 1.25) return t('engines.vram.tight');
  return t('engines.vram.fits');
}

function statusLabel(status: string): string {
  const labels: Record<string, string> = {
    missing: t('engines.status.missing'),
    installing: t('engines.status.installing'),
    installed: t('engines.status.installed'),
    broken: t('engines.status.broken'),
    external: t('engines.status.external'),
  };
  return labels[status] ?? status;
}

export function EngineCard({ engine, gpu, onAction, busy = false, highlighted = false }: Props): React.JSX.Element {
  const [confirmExternal, setConfirmExternal] = useState(false);
  const [typedName, setTypedName] = useState('');
  const external = engine.owner === 'external' || engine.status === 'external';
  const managed = engine.owner === 'app';
  const installed = engine.status === 'installed' || engine.status === 'external';
  const canInstall = Boolean(gpu) || engine.cpu;
  const verification = engine.verification as { ok?: boolean } | null;

  const uninstall = () => {
    if (external) {
      setConfirmExternal(true);
      return;
    }
    if (window.confirm(t('engines.uninstall.app_confirm', { engine: engine.engine, size: installedSize(engine) }))) {
      onAction({ type: 'uninstall', engine: engine.engine });
    }
  };

  return (
    <UICard id={`engine-card-${engine.engine}`} aria-label={engine.engine} className={highlighted ? 'ring-2 ring-primary' : undefined}>
      <UIStack gap="sm">
        <UIStack direction="row" justify="between" align="start" className="flex-wrap">
          <UIStack gap="xs">
            <UIText variant="heading">{engine.engine}</UIText>
            <UIStack direction="row" gap="xs" className="flex-wrap">
              <UIBadge>{statusLabel(engine.status)}</UIBadge>
              {external ? <UIBadge tone="brand">{t('engines.status.external')}</UIBadge> : null}
              <UIBadge tone={engine.commercial ? 'accent' : 'danger'}>{engine.license}</UIBadge>
            </UIStack>
          </UIStack>
          <UIText variant="caption">
            {t(engine.size_bytes > 0 ? 'engines.size.actual' : 'engines.size.estimated', { size: installedSize(engine) })}
          </UIText>
        </UIStack>

        <UIStack direction="row" gap="sm" className="flex-wrap">
          <UIBadge tone={vramLabel(engine.vram_gb, gpu) === t('engines.vram.no_fit') ? 'danger' : 'neutral'}>
            {gpu ? `${vramLabel(engine.vram_gb, gpu)} · ${engine.vram_gb} / ${gpu.vram_gb} GB` : vramLabel(engine.vram_gb, gpu)}
          </UIBadge>
          <UIBadge tone={engine.cpu ? 'accent' : 'neutral'}>
            {engine.cpu ? t('engines.cpu.supported') : t('engines.cpu.gpu_required')}
          </UIBadge>
        </UIStack>

        <UIText variant="caption">
          {verification ? (verification.ok ? t('engines.verification.ok') : t('engines.verification.failed')) : t('engines.verification.pending')}
        </UIText>

        <UIStack direction="row" gap="sm" className="flex-wrap">
          {engine.status === 'missing' ? (
            <UIButton disabled={!canInstall || busy} onClick={() => onAction({ type: 'install', engine: engine.engine })}>
              {t('engines.action.install')}
            </UIButton>
          ) : null}
          {installed ? (
            <>
              <UIButton variant="secondary" disabled={busy} onClick={() => onAction({ type: 'verify', engine: engine.engine })}>
                {t('engines.action.verify')}
              </UIButton>
              {managed ? (
                <UIButton variant="secondary" disabled={busy} onClick={() => onAction({ type: 'repair', engine: engine.engine })}>
                  {t('engines.action.repair')}
                </UIButton>
              ) : null}
              <UIButton variant="danger" disabled={busy} onClick={uninstall}>
                {t('engines.action.uninstall')}
              </UIButton>
            </>
          ) : null}
          {engine.status === 'broken' && managed ? (
            <UIButton variant="secondary" disabled={busy} onClick={() => onAction({ type: 'repair', engine: engine.engine })}>
              {t('engines.action.repair')}
            </UIButton>
          ) : null}
          {engine.status === 'installing' ? <UIText variant="caption">{t('engines.status.installing')}</UIText> : null}
        </UIStack>

        {confirmExternal ? (
          <UIStack gap="sm">
            <UIText variant="caption">{t('engines.uninstall.external_warning', { size: installedSize(engine) })}</UIText>
            <UIField label={t('engines.uninstall.type_name')} value={typedName} onChange={(event) => setTypedName(event.target.value)} />
            <UIStack direction="row" gap="sm">
              <UIButton
                variant="danger"
                disabled={busy || typedName !== engine.engine}
                onClick={() => onAction({ type: 'uninstall', engine: engine.engine, force: true })}
              >
                {t('engines.uninstall.confirm')}
              </UIButton>
              <UIButton variant="ghost" onClick={() => { setConfirmExternal(false); setTypedName(''); }}>
                {t('action.cancel')}
              </UIButton>
            </UIStack>
          </UIStack>
        ) : null}

        {!gpu && !engine.cpu ? <UIText variant="caption">{t('engines.cpu.no_gpu')}</UIText> : null}
        {gpu && gpu.vram_gb < engine.vram_gb && engine.status === 'missing' ? (
          <UIText variant="caption">{t('engines.vram.install_warning')}</UIText>
        ) : null}
      </UIStack>
    </UICard>
  );
}

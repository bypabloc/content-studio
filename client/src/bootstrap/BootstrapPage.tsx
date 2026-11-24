import { openPath } from '@tauri-apps/plugin-opener';

import { UIButton } from '@/shared/components/atoms/UIButton';
import { UIPage } from '@/shared/components/atoms/UIPage';
import { UIStack } from '@/shared/components/atoms/UIStack';
import { UIText } from '@/shared/components/atoms/UIText';
import { t } from '@/shared/i18n/t';

import type { BootstrapProgress, BootstrapState, BootstrapStep } from './useBootstrapProgress';

const STEPS: BootstrapStep[] = ['python', 'sync', 'seed'];

function stepLabel(step: BootstrapStep): string {
  if (step === 'python') return t('bootstrap.step.python');
  if (step === 'sync') return t('bootstrap.step.sync');
  return t('bootstrap.step.seed');
}

function stateLabel(state: BootstrapState | undefined): string {
  if (state === 'running') return t('bootstrap.state.running');
  if (state === 'done') return t('bootstrap.state.done');
  if (state === 'skipped') return t('bootstrap.state.skipped');
  if (state === 'failed') return t('bootstrap.state.failed');
  return t('bootstrap.state.pending');
}

/** El motivo de un código `bootstrap_<paso>_failed` que devuelve `get_connection`. */
function reason(code: string): string {
  if (code === 'bootstrap_python_failed') return t('bootstrap.error.python');
  if (code === 'bootstrap_sync_failed') return t('bootstrap.error.sync');
  return t('bootstrap.error.seed');
}

interface Props extends BootstrapProgress {
  failed: string | null;
  onRetry: () => void;
}

/**
 * La preparación del primer arranque de la app instalada (spec 022, D-2): Python, las librerías del motor y los datos,
 * con el estado de cada paso. Si uno falla, el motivo, «Reintentar» (los pasos hechos no se repiten) y «Ver log».
 */
export function BootstrapPage({ steps, log, failed, onRetry }: Props): React.JSX.Element {
  return (
    <UIPage className="flex-col gap-2 select-none">
      <UIText variant="title">{t('bootstrap.title')}</UIText>
      <UIText variant="caption">{t('bootstrap.hint')}</UIText>
      <UIStack gap="xs">
        {STEPS.map((step) => (
          <UIText key={step} variant="body">{`${stepLabel(step)}: ${stateLabel(steps[step])}`}</UIText>
        ))}
      </UIStack>
      {failed ? (
        <UIStack gap="sm">
          <UIText variant="body">{reason(failed)}</UIText>
          <UIStack direction="row" gap="sm">
            <UIButton variant="secondary" onClick={onRetry}>
              {t('server.retry')}
            </UIButton>
            {log ? (
              <UIButton variant="secondary" onClick={() => void openPath(log)}>
                {t('bootstrap.log')}
              </UIButton>
            ) : null}
          </UIStack>
        </UIStack>
      ) : null}
    </UIPage>
  );
}

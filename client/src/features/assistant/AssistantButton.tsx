import { UIButton } from '@/shared/components/atoms/UIButton';
import { UILink } from '@/shared/components/atoms/UILink';
import { UIStack } from '@/shared/components/atoms/UIStack';
import { UIText } from '@/shared/components/atoms/UIText';
import { type MessageKey, t } from '@/shared/i18n/t';

import { assistantReady, useAssistantStatus } from './useAssistant';

interface Props {
  label: string;
  busy: boolean;
  error: string | null;
  disabled?: boolean;
  onClick: () => void;
}

/**
 * Un botón de IA (spec 021, D-5). Con el asistente apagado en Ajustes no aparece; sin el modelo instalado lleva a
 * Motores; mientras el trabajo carga el modelo y responde, dice «Cargando el asistente…». El error va debajo.
 */
export function AssistantButton({ label, busy, error, disabled = false, onClick }: Props): React.JSX.Element | null {
  const status = useAssistantStatus();
  if (!status.data?.enabled) return null;
  if (!assistantReady(status.data)) {
    return (
      <UILink variant="secondary" icon="bot" href="#/engines?engine=llama-cpp">
        {t('llm.install')}
      </UILink>
    );
  }
  return (
    <UIStack gap="sm">
      <UIButton variant="secondary" icon="bot" disabled={busy || disabled} onClick={onClick}>
        {busy ? t('llm.loading') : label}
      </UIButton>
      {error ? <UIText variant="caption">{t(`error.${error}` as MessageKey)}</UIText> : null}
    </UIStack>
  );
}

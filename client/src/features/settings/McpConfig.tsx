import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';
import { useApi } from '@/shared/api/context';
import type { components } from '@/shared/api/schema';
import { UIButton } from '@/shared/components/atoms/UIButton';
import { UIStack } from '@/shared/components/atoms/UIStack';
import { UIText } from '@/shared/components/atoms/UIText';
import { UISelect, type UISelectOption } from '@/shared/components/molecules/UISelect';
import { t } from '@/shared/i18n/t';

type McpConfigOut = components['schemas']['McpConfigOut'];

// Nombres propios de cada aplicación (no se traducen). El valor es el que pide GET /integrations/mcp-config.
const CLIENTS: UISelectOption[] = [
  { value: 'claude-code', label: 'Claude Code' }, // i18n-ignore: nombre propio de la aplicación
  { value: 'codex', label: 'Codex' }, // i18n-ignore: nombre propio de la aplicación
  { value: 'vscode', label: 'VS Code' }, // i18n-ignore: nombre propio de la aplicación
  { value: 'cursor', label: 'Cursor' }, // i18n-ignore: nombre propio de la aplicación
  { value: 'claude-desktop', label: 'Claude Desktop' }, // i18n-ignore: nombre propio de la aplicación
  { value: 'lm-studio', label: 'LM Studio' }, // i18n-ignore: nombre propio de la aplicación
  { value: 'jan', label: 'Jan' }, // i18n-ignore: nombre propio de la aplicación
  { value: 'anythingllm', label: 'AnythingLLM' }, // i18n-ignore: nombre propio de la aplicación
];

/**
 * Ajustes > Integraciones (spec 029, AC-10): elige la aplicación y copia su fragmento MCP. El fragmento lo arma la API
 * con la ruta de `studio mcp` de esta instalación.
 */
export function McpConfig() {
  const api = useApi();
  const [client, setClient] = useState(CLIENTS[0].value);
  const config = useQuery({
    queryKey: ['integrations', 'mcp-config', client],
    queryFn: () => api.get<McpConfigOut>(`/integrations/mcp-config?client=${client}`),
  });

  const fragment = config.data?.fragment ?? '';

  return (
    <UIStack gap="sm">
      <UIText variant="heading">{t('settings.integrations.mcp_title')}</UIText>
      <UISelect label={t('settings.integrations.mcp_client')} options={CLIENTS} value={client} onChange={setClient} />
      <UIButton variant="secondary" className="self-start" disabled={!config.data} onClick={() => void navigator.clipboard.writeText(fragment)}>
        {t('settings.integrations.mcp_copy')}
      </UIButton>
    </UIStack>
  );
}

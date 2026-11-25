import { invoke } from '@tauri-apps/api/core';
import { useState } from 'react';
import { useApi } from '@/shared/api/context';
import { UIButton } from '@/shared/components/atoms/UIButton';
import { UIStack } from '@/shared/components/atoms/UIStack';
import { UIText } from '@/shared/components/atoms/UIText';
import { UIField } from '@/shared/components/molecules/UIField';
import { useSetting } from '@/shared/hooks/useSetting';
import { t } from '@/shared/i18n/t';

import { InboxFolders } from './InboxFolders';
import { McpConfig } from './McpConfig';

const DEFAULT_PORT = 41830;
const DEFAULT_IDLE_MINUTES = 10;

/**
 * Ajustes > Integraciones (spec 028, AC-11): la dirección del server compartido, su puerto, sus minutos sin uso antes de
 * apagarse, y el token para las apps conectadas (copiarlo o cambiarlo). Cambiar el token detiene el server: la app se
 * reconecta sola y el token nuevo sale en la conexión.
 */
export function IntegrationsPanel() {
  const api = useApi();
  const [port, setPort] = useSetting('api.port', DEFAULT_PORT);
  const [idleMinutes, setIdleMinutes] = useSetting('api.idle_minutes', DEFAULT_IDLE_MINUTES);
  const [failed, setFailed] = useState(false);

  const copyToken = () => {
    void navigator.clipboard.writeText(api.connection.token);
  };

  const rotateToken = async () => {
    if (!window.confirm(t('settings.integrations.rotate_confirm'))) return;
    setFailed(false);
    try {
      await invoke('rotate_token');
      await api.reconnect();
    } catch {
      setFailed(true);
    }
  };

  return (
    <UIStack gap="md">
      <UIText variant="heading">{t('settings.integrations.title')}</UIText>
      <UIStack gap="xs">
        <UIText variant="caption">{t('settings.integrations.url')}</UIText>
        <UIText variant="body">{api.connection.baseUrl}</UIText>
      </UIStack>
      <UIField
        label={t('settings.integrations.port')}
        type="number"
        min={1024}
        max={65535}
        value={port}
        onChange={(event) => setPort(Number(event.target.value))}
      />
      <UIField
        label={t('settings.integrations.idle', { minutes: idleMinutes })}
        type="number"
        min={1}
        value={idleMinutes}
        onChange={(event) => setIdleMinutes(Number(event.target.value))}
      />
      <UIStack gap="sm">
        <UIButton variant="secondary" className="self-start" onClick={copyToken}>
          {t('settings.integrations.copy_token')}
        </UIButton>
        <UIButton variant="secondary" className="self-start" onClick={() => void rotateToken()}>
          {t('settings.integrations.rotate_token')}
        </UIButton>
      </UIStack>
      {failed && <UIText variant="caption">{t('settings.integrations.rotate_failed')}</UIText>}
      <McpConfig />
      <InboxFolders />
    </UIStack>
  );
}

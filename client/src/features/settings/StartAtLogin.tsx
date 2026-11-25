import { invoke } from '@tauri-apps/api/core';

import { UICheckbox } from '@/shared/components/atoms/UICheckbox';
import { UIStack } from '@/shared/components/atoms/UIStack';
import { UIText } from '@/shared/components/atoms/UIText';
import { toast } from '@/shared/components/molecules/UIToast';
import { useSetting } from '@/shared/hooks/useSetting';
import { t } from '@/shared/i18n/t';

/** «Iniciar el servidor con Windows» (spec 031, AC-8): el valor `Run` de HKCU arranca el server con la sesión. */
export function StartAtLogin(): React.JSX.Element {
  const [enabled, setEnabled] = useSetting<boolean>('system.start_at_login', false);

  async function change(value: boolean): Promise<void> {
    try {
      await invoke('set_start_at_login', { enabled: value });
      setEnabled(value);
    } catch {
      toast.error(t('settings.system.start_at_login_error'));
    }
  }

  return (
    <UIStack gap="md">
      <UIText variant="heading">{t('settings.system.title')}</UIText>
      <UICheckbox label={t('settings.system.start_at_login')} checked={enabled} onChange={(value) => void change(value)} />
      <UIText variant="caption">{t('settings.system.start_at_login_help')}</UIText>
    </UIStack>
  );
}

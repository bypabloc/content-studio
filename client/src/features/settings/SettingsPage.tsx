import { useQueryClient } from '@tanstack/react-query';
import { AssistantSettings } from '@/features/assistant/AssistantSettings';
import { MicrophonePicker } from '@/features/recording/MicrophonePicker';
import { StorageSettings } from './StorageSettings';
import { MICROPHONE_SETTING } from '@/features/recording/microphones';
import { RECORDING_LOG, useRecordingLog } from '@/features/recording/recordingLog';
import { useApi } from '@/shared/api/context';
import { UIButton } from '@/shared/components/atoms/UIButton';
import { UICheckbox } from '@/shared/components/atoms/UICheckbox';
import { UIStack } from '@/shared/components/atoms/UIStack';
import { UIText } from '@/shared/components/atoms/UIText';
import { UISelect } from '@/shared/components/molecules/UISelect';
import { THEME_ICONS } from '@/shared/components/molecules/UIThemeToggle';
import { useSetting } from '@/shared/hooks/useSetting';
import { t } from '@/shared/i18n/t';
import type { LanguagePreference } from '@/shared/i18n/locale';
import { useLanguage } from '@/shared/i18n/useLanguage';
import { useTheme } from '@/shared/theme/useTheme';
import type { ThemeMode } from '@/shared/theme/theme';

/**
 * Ajustes: apariencia (idioma y tema), avisos, micrófono (spec 010, D-2), registro del micrófono (apagado por defecto,
 * spec 010, D-7), restablecer las elecciones de los selectores (con confirmación) y la lista de atajos. El idioma y el tema
 * se guardan en `ui.*`, así que «Restablecer» no los toca.
 */
export function SettingsPage() {
  const api = useApi();
  const queryClient = useQueryClient();
  const [language, setLanguage] = useLanguage();
  const [theme, setTheme] = useTheme();
  const [notifySystem, setNotifySystem] = useSetting('notify.system', true);
  const [notifySound, setNotifySound] = useSetting('notify.sound', true);
  const [microphone, setMicrophone] = useSetting(MICROPHONE_SETTING, '');
  const [recordingLog, setRecordingLog] = useSetting(RECORDING_LOG, false);
  const log = useRecordingLog();

  const reset = async () => {
    if (!window.confirm(t('settings.reset_confirm'))) return;
    await api.del(`/settings?prefix=${encodeURIComponent('select.')}`);
    await queryClient.invalidateQueries({ queryKey: ['settings'] });
  };

  const shortcuts = [t('settings.shortcut_palette'), t('settings.shortcut_generate'), t('settings.shortcut_play')];

  return (
    <UIStack gap="lg" className="max-w-xl">
      <UIStack gap="md">
        <UIText variant="heading">{t('settings.appearance')}</UIText>
        <UISelect
          label={t('settings.language')}
          options={[
            { value: 'system', label: `★ ${t('language.system')}` },
            { value: 'es', label: t('language.es') },
            { value: 'en', label: t('language.en') },
            { value: 'pt', label: t('language.pt') },
          ]}
          value={language}
          onChange={(value) => setLanguage(value as LanguagePreference)}
        />
        <UISelect
          label={t('settings.theme')}
          options={[
            { value: 'light', label: t('theme.light'), icon: THEME_ICONS.light },
            { value: 'dark', label: t('theme.dark'), icon: THEME_ICONS.dark },
            { value: 'system', label: t('theme.system'), icon: THEME_ICONS.system },
          ]}
          value={theme}
          onChange={(value) => setTheme(value as ThemeMode)}
        />
      </UIStack>

      <UIStack gap="md">
        <UIText variant="heading">{t('settings.notifications')}</UIText>
        <UICheckbox label={t('settings.notify_system')} checked={notifySystem} onChange={setNotifySystem} />
        <UICheckbox label={t('settings.notify_sound')} checked={notifySound} onChange={setNotifySound} />
      </UIStack>

      <UIStack gap="md">
        <UIText variant="heading">{t('settings.microphone')}</UIText>
        <MicrophonePicker value={microphone} onChange={setMicrophone} log={log} />
      </UIStack>

      <UIStack gap="md">
        <UIText variant="heading">{t('settings.logs')}</UIText>
        <UICheckbox label={t('settings.log_recording')} checked={recordingLog} onChange={setRecordingLog} />
        <UIText variant="caption">{t('settings.log_recording_hint')}</UIText>
      </UIStack>

      <UIStack gap="md">
        <UIText variant="heading">{t('settings.shortcuts')}</UIText>
        <UIStack role="list" gap="sm">
          {shortcuts.map((shortcut) => (
            <UIStack key={shortcut} role="listitem">
              <UIText variant="body">{shortcut}</UIText>
            </UIStack>
          ))}
        </UIStack>
      </UIStack>

      <UIStack>
        <UIButton variant="secondary" icon="history" className="self-start" onClick={() => void reset()}>
          {t('settings.reset')}
        </UIButton>
      </UIStack>

      <AssistantSettings />

      <StorageSettings />
    </UIStack>
  );
}

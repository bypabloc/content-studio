import { useQueryClient } from '@tanstack/react-query';
import { useApi } from '@/shared/api/context';
import { useSetting } from '@/shared/hooks/useSetting';
import { t } from '@/shared/i18n/t';
import type { LanguagePreference } from '@/shared/i18n/locale';
import { useLanguage } from '@/shared/i18n/useLanguage';
import { useTheme } from '@/shared/theme/useTheme';
import type { ThemeMode } from '@/shared/theme/theme';

/**
 * Ajustes: apariencia (idioma y tema), avisos, restablecer las elecciones de los selectores (con confirmación) y la
 * lista de atajos. El idioma y el tema se guardan en `ui.*`, así que «Restablecer» no los toca.
 */
export function SettingsPage() {
  const api = useApi();
  const queryClient = useQueryClient();
  const [language, setLanguage] = useLanguage();
  const [theme, setTheme] = useTheme();
  const [notifySystem, setNotifySystem] = useSetting('notify.system', true);
  const [notifySound, setNotifySound] = useSetting('notify.sound', true);

  const reset = async () => {
    if (!window.confirm(t('settings.reset_confirm'))) return;
    await api.del(`/settings?prefix=${encodeURIComponent('select.')}`);
    await queryClient.invalidateQueries({ queryKey: ['settings'] });
  };

  return (
    <div className="flex max-w-xl flex-col gap-8">
      <section className="flex flex-col gap-3">
        <h3 className="text-sm font-medium">{t('settings.appearance')}</h3>
        <div className="flex items-center justify-between gap-4 text-sm">
          <span>{t('settings.language')}</span>
          <select
            aria-label={t('settings.language')}
            value={language}
            onChange={(event) => setLanguage(event.target.value as LanguagePreference)}
            className="rounded-md border border-input bg-transparent px-2 py-1.5"
          >
            <option value="system">{`★ ${t('language.system')}`}</option>
            <option value="es">{t('language.es')}</option>
            <option value="en">{t('language.en')}</option>
            <option value="pt">{t('language.pt')}</option>
          </select>
        </div>
        <div className="flex items-center justify-between gap-4 text-sm">
          <span>{t('settings.theme')}</span>
          <select
            aria-label={t('settings.theme')}
            value={theme}
            onChange={(event) => setTheme(event.target.value as ThemeMode)}
            className="rounded-md border border-input bg-transparent px-2 py-1.5"
          >
            <option value="light">{t('theme.light')}</option>
            <option value="dark">{t('theme.dark')}</option>
            <option value="system">{t('theme.system')}</option>
          </select>
        </div>
      </section>

      <section className="flex flex-col gap-3">
        <h3 className="text-sm font-medium">{t('settings.notifications')}</h3>
        <label className="flex items-center gap-2 text-sm">
          <input type="checkbox" checked={notifySystem} onChange={(event) => setNotifySystem(event.target.checked)} />
          {t('settings.notify_system')}
        </label>
        <label className="flex items-center gap-2 text-sm">
          <input type="checkbox" checked={notifySound} onChange={(event) => setNotifySound(event.target.checked)} />
          {t('settings.notify_sound')}
        </label>
      </section>

      <section className="flex flex-col gap-3">
        <h3 className="text-sm font-medium">{t('settings.shortcuts')}</h3>
        <ul className="flex list-disc flex-col gap-1 pl-5 text-sm">
          <li>{t('settings.shortcut_palette')}</li>
          <li>{t('settings.shortcut_generate')}</li>
          <li>{t('settings.shortcut_play')}</li>
        </ul>
      </section>

      <section>
        <button
          type="button"
          onClick={() => void reset()}
          className="rounded-md border border-border px-3 py-1.5 text-sm hover:bg-accent"
        >
          {t('settings.reset')}
        </button>
      </section>
    </div>
  );
}

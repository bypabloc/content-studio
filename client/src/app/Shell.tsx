import { NarrationPage } from '@/features/narration/NarrationPage';
import { MusicPage } from '@/features/music/MusicPage';
import { QueuePanel } from '@/features/queue/QueuePanel';
import { SettingsPage } from '@/features/settings/SettingsPage';
import { CatalogPage } from '@/features/voices/CatalogPage';
import { MyVoicesPage } from '@/features/voices/MyVoicesPage';
import { UIText } from '@/shared/components/atoms/UIText';
import { nextTheme, UIThemeToggle } from '@/shared/components/molecules/UIThemeToggle';
import { UIToaster } from '@/shared/components/molecules/UIToast';
import { UIAppShell } from '@/shared/components/organisms/UIAppShell';
import { UICommandPalette } from '@/shared/components/organisms/UICommandPalette';
import { useSectionId } from '@/shared/hooks/useSectionId';
import { useSetting } from '@/shared/hooks/useSetting';
import { t } from '@/shared/i18n/t';
import { useLanguage } from '@/shared/i18n/useLanguage';
import { useTheme } from '@/shared/theme/useTheme';
import { navItems } from './nav';

/** La ventana ya conectada: la barra con las secciones, la cola y el tema; la paleta con Ctrl+K y los avisos. */
export function Shell({ version }: { version: string }) {
  useLanguage(); // aplica al idioma activo la preferencia del server (ui.language), una vez por la vida de la ventana
  const [theme, setTheme] = useTheme();
  const [collapsed, setCollapsed] = useSetting<boolean>('ui.sidebar.collapsed', false);
  const sectionId = useSectionId();
  const nav = navItems();
  const section = nav.find((item) => item.id === sectionId);
  const modes = { light: t('theme.light'), dark: t('theme.dark'), system: t('theme.system') };

  return (
    <>
      <UIAppShell
        brand={<UIText variant="title">{t('app.name')}</UIText>}
        nav={nav}
        aside={<QueuePanel />}
        footer={
          <>
            <UIThemeToggle
              theme={theme}
              onThemeChange={setTheme}
              labels={{ toggle: t('theme.change', { mode: modes[theme], next: modes[nextTheme(theme)] }) }}
            />
            <UIText variant="caption" className="group-data-[collapsible=icon]:hidden">
              {t('app.version', { version })}
            </UIText>
          </>
        }
        collapsed={collapsed}
        onCollapsedChange={setCollapsed}
        labels={{ skip: t('shell.skip'), toggle: t('shell.toggle'), title: t('nav.label') }}
      >
        {section ? <UIText variant="subtitle">{section.label}</UIText> : null}
        {section?.id === 'narration' && <NarrationPage />}
        {section?.id === 'music' && <MusicPage />}
        {section?.id === 'voices' && <MyVoicesPage />}
        {section?.id === 'catalog' && <CatalogPage />}
        {section?.id === 'settings' && <SettingsPage />}
        {!section && <UIText variant="caption">{t('shell.empty')}</UIText>}
      </UIAppShell>
      <UICommandPalette
        items={nav}
        onSelect={(id) => {
          window.location.hash = `#/${id}`;
        }}
        labels={{ title: t('palette.title'), placeholder: t('palette.placeholder'), empty: t('palette.empty') }}
      />
      <UIToaster label={t('notify.region')} />
    </>
  );
}

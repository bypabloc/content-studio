import { lazy, Suspense } from 'react';
import { NarrationPage } from '@/features/narration/NarrationPage';
import { QueuePanel } from '@/features/queue/QueuePanel';
import { CatalogPage } from '@/features/voices/CatalogPage';
import { MyVoicesPage } from '@/features/voices/MyVoicesPage';
import { UISkeleton } from '@/shared/components/atoms/UISkeleton';
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

// La página de Música solo se carga al abrirla: así el JS de arranque queda bajo el presupuesto de client/budget.json.
const MusicPage = lazy(() => import('@/features/music/MusicPage').then((module) => ({ default: module.MusicPage })));
const CleanerPage = lazy(() => import('@/features/cleaner/CleanerPage').then((module) => ({ default: module.CleanerPage })));
const EnginesPage = lazy(() => import('@/features/engines/EnginesPage').then((module) => ({ default: module.EnginesPage })));
const SettingsPage = lazy(() => import('@/features/settings/SettingsPage').then((module) => ({ default: module.SettingsPage })));
const SubtitlesPage = lazy(() => import('@/features/subtitles/SubtitlesPage').then((module) => ({ default: module.SubtitlesPage })));
const WelcomeGate = lazy(() => import('@/features/welcome/WelcomeGate').then((module) => ({ default: module.WelcomeGate })));

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
        {section?.id === 'music' && (
          <Suspense fallback={<UISkeleton className="h-64 w-full rounded-xl" />}>
            <MusicPage />
          </Suspense>
        )}
        {section?.id === 'cleaner' && (
          <Suspense fallback={<UISkeleton className="h-64 w-full rounded-xl" />}>
            <CleanerPage />
          </Suspense>
        )}
        {section?.id === 'engines' && (
          <Suspense fallback={<UISkeleton className="h-64 w-full rounded-xl" />}>
            <EnginesPage />
          </Suspense>
        )}
        {section?.id === 'voices' && <MyVoicesPage />}
        {section?.id === 'catalog' && <CatalogPage />}
        {section?.id === 'subtitles' && (
          <Suspense fallback={<UISkeleton className="h-64 w-full rounded-xl" />}>
            <SubtitlesPage />
          </Suspense>
        )}
        {section?.id === 'settings' && (
          <Suspense fallback={<UISkeleton className="h-64 w-full rounded-xl" />}>
            <SettingsPage />
          </Suspense>
        )}
        {!section && <UIText variant="caption">{t('shell.empty')}</UIText>}
      </UIAppShell>
      <Suspense fallback={null}><WelcomeGate /></Suspense>
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

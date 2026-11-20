import { Toaster } from 'sonner';
import { NarrationPage } from '@/features/narration/NarrationPage';
import { QueuePanel } from '@/features/queue/QueuePanel';
import { SettingsPage } from '@/features/settings/SettingsPage';
import { t } from '@/shared/i18n/t';
import { useLanguage } from '@/shared/i18n/useLanguage';
import { useTheme } from '@/shared/theme/useTheme';
import { CommandPalette } from './CommandPalette';
import { navItems } from './nav';
import { useSectionId } from './routes';
import { Sidebar } from './Sidebar';
import { ThemeToggle } from './ThemeToggle';

/** La ventana ya conectada: sidebar con las secciones, pie con el tema, y la paleta con Ctrl+K. */
export function Shell({ version }: { version: string }) {
  useLanguage(); // aplica al idioma activo la preferencia del server (ui.language), una vez por la vida de la ventana
  const [theme, setTheme] = useTheme();
  const sectionId = useSectionId();
  const section = navItems().find((item) => item.id === sectionId);

  return (
    <div className="flex min-h-screen select-none">
      <aside className="flex w-56 flex-col gap-6 border-r border-border p-4">
        <header>
          <h1 className="text-lg font-semibold">{t('app.name')}</h1>
          <p className="text-xs text-muted-foreground">{t('app.version', { version })}</p>
        </header>
        <Sidebar />
        <QueuePanel />
        <div className="mt-auto">
          <ThemeToggle mode={theme} onChange={setTheme} />
        </div>
      </aside>
      <main className="flex flex-1 flex-col gap-2 p-6">
        {section ? <h2 className="text-xl font-semibold">{section.label}</h2> : null}
        {section?.id === 'narration' && <NarrationPage />}
        {section?.id === 'settings' && <SettingsPage />}
        {!section && <p className="text-sm text-muted-foreground">{t('shell.empty')}</p>}
      </main>
      <CommandPalette />
      <Toaster theme={theme} containerAriaLabel={t('notify.region')} />
    </div>
  );
}

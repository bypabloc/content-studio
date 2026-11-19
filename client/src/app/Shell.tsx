import { useEffect } from 'react';
import { Toaster } from 'sonner';
import { QueuePanel } from '@/features/queue/QueuePanel';
import { SettingsPage } from '@/features/settings/SettingsPage';
import { t } from '@/shared/i18n/t';
import { useTheme } from '@/shared/theme/useTheme';
import { CommandPalette } from './CommandPalette';
import { blockContextMenu } from './native';
import { NAV } from './nav';
import { useSectionId } from './routes';
import { Sidebar } from './Sidebar';
import { ThemeToggle } from './ThemeToggle';

/** La ventana ya conectada: sidebar con las secciones, pie con el tema, y la paleta con Ctrl+K. */
export function Shell({ version }: { version: string }) {
  const [theme, setTheme] = useTheme();
  const sectionId = useSectionId();
  const section = NAV.find((item) => item.id === sectionId);

  useEffect(() => {
    document.addEventListener('contextmenu', blockContextMenu);
    return () => document.removeEventListener('contextmenu', blockContextMenu);
  }, []);

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
        {section?.id === 'settings' ? <SettingsPage /> : <p className="text-sm text-muted-foreground">{t('shell.empty')}</p>}
      </main>
      <CommandPalette />
      <Toaster />
    </div>
  );
}

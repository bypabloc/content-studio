import { t } from '@/shared/i18n/t';

export const APP_VERSION = '0.1.0';

export function App() {
  return (
    <main className="flex min-h-screen select-none flex-col items-center justify-center gap-2">
      <h1 className="text-2xl font-semibold">{t('app.name')}</h1>
      <p className="text-sm text-muted-foreground">{t('app.version', { version: APP_VERSION })}</p>
    </main>
  );
}

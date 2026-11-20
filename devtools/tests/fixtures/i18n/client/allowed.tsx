import { t } from '@/shared/i18n/t';

type Theme = 'light' | 'dark';

export function Bar({ id }: { id: string }) {
  console.debug('state', id);
  return (
    <div className="flex gap-2" data-testid="job-row" role="list">
      <span>{t('nav.settings')}</span>
      <a href="/ajustes">x</a>
      <i style={{}} aria-controls="panel">x</i>
      <input type="text" name="q" />
      <span aria-label={t('nav.settings')} />
    </div>
  );
}

const ignored = 'Hola mundo'; // i18n-ignore: test fixture, not visible text

import { t } from '@/shared/i18n/t';
import type { ThemeMode } from '@/shared/theme/theme';

const NEXT: Record<ThemeMode, ThemeMode> = { light: 'dark', dark: 'system', system: 'light' };

function modeLabel(mode: ThemeMode): string {
  switch (mode) {
    case 'light':
      return t('theme.light');
    case 'dark':
      return t('theme.dark');
    default:
      return t('theme.system');
  }
}

/** Botón rápido del pie de la sidebar: cada pulsación pasa al modo siguiente. El campo completo va en Ajustes. */
export function ThemeToggle({ mode, onChange }: { mode: ThemeMode; onChange: (mode: ThemeMode) => void }) {
  return (
    <button
      type="button"
      aria-label={t('theme.change', { mode: modeLabel(mode) })}
      onClick={() => onChange(NEXT[mode])}
      className="rounded-md border border-border px-3 py-1.5 text-sm hover:bg-accent"
    >
      {modeLabel(mode)}
    </button>
  );
}

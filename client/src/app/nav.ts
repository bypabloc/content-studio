import { t } from '@/shared/i18n/t';

export interface NavItem {
  id: string;
  group: string;
  label: string;
}

/** Las secciones de la app, en orden. Cada spec agrega su línea (D-3): el menú y la paleta salen de aquí. */
export const NAV: NavItem[] = [
  { id: 'narration', group: t('nav.group.generate'), label: t('nav.narration') },
  { id: 'settings', group: t('nav.group.settings'), label: t('nav.settings') },
];

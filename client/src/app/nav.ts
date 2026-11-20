import { t } from '@/shared/i18n/t';

export interface NavItem {
  id: string;
  group: string;
  label: string;
}

/**
 * Las secciones de la app, en orden. Cada spec agrega su línea (D-3): el menú y la paleta salen de aquí.
 * Es una función, no una constante: las etiquetas cambian con el idioma activo.
 */
export function navItems(): NavItem[] {
  return [
    { id: 'narration', group: t('nav.group.generate'), label: t('nav.narration') },
    { id: 'settings', group: t('nav.group.settings'), label: t('nav.settings') },
  ];
}

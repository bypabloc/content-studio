import type { IconName } from '@/shared/components/atoms/UIIcon';
import { t } from '@/shared/i18n/t';

export interface NavItem {
  id: string;
  group: string;
  label: string;
  icon: IconName;
}

/**
 * Las secciones de la app, en orden. Cada spec agrega su línea (D-3): el menú y la paleta salen de aquí.
 * Es una función, no una constante: las etiquetas cambian con el idioma activo.
 */
export function navItems(): NavItem[] {
  return [
    { id: 'narration', group: t('nav.group.generate'), label: t('nav.narration'), icon: 'narration' },
    { id: 'music', group: t('nav.group.generate'), label: t('nav.music'), icon: 'music' },
    { id: 'cleaner', group: t('nav.group.edit'), label: t('nav.cleaner'), icon: 'scissors' },
    { id: 'subtitles', group: t('nav.group.edit'), label: t('nav.subtitles'), icon: 'subtitles' },
    { id: 'convert', group: t('nav.group.edit'), label: t('nav.convert'), icon: 'download' },
    { id: 'normalize', group: t('nav.group.edit'), label: t('nav.normalize'), icon: 'volume' },
    { id: 'mix', group: t('nav.group.edit'), label: t('nav.mix'), icon: 'mix' },
    { id: 'editor', group: t('nav.group.edit'), label: t('nav.editor'), icon: 'editor' },
    { id: 'library', group: t('nav.group.edit'), label: t('nav.library'), icon: 'library' },
    { id: 'voices', group: t('nav.group.voices'), label: t('nav.voices'), icon: 'voices' },
    { id: 'catalog', group: t('nav.group.voices'), label: t('nav.catalog'), icon: 'layers' },
    { id: 'engines', group: t('nav.group.settings'), label: t('nav.engines'), icon: 'server' },
    { id: 'settings', group: t('nav.group.settings'), label: t('nav.settings'), icon: 'settings' },
  ];
}

import { useMemo, useState } from 'react';

import type { components } from '@/shared/api/schema';
import { UIButton } from '@/shared/components/atoms/UIButton';
import { UIStack } from '@/shared/components/atoms/UIStack';
import { UIText } from '@/shared/components/atoms/UIText';
import { UIField } from '@/shared/components/molecules/UIField';
import { label, t } from '@/shared/i18n/t';

import { StyleCard } from './StyleCard';

type StyleOut = components['schemas']['StyleOut'];
type Mode = 'all' | 'major' | 'minor';

interface Filters {
  query: string;
  category: string | null;
  mode: Mode;
  min: number;
  max: number;
}

/** ¿El preset pasa los filtros? La búsqueda mira la clave, la descripción y el nombre visible. */
function matches(style: StyleOut, filters: Filters): boolean {
  const text = `${style.key} ${style.caption} ${label('music.style', style.key)}`.toLowerCase();
  const query = filters.query.trim().toLowerCase();
  return (
    (query === '' || text.includes(query)) &&
    (filters.category === null || style.category === filters.category) &&
    (filters.mode === 'all' || (filters.mode === 'major') === style.musical_key.endsWith('Major')) && // i18n-ignore: sufijo de la tonalidad de los presets, no es texto visible
    style.bpm >= filters.min &&
    style.bpm <= filters.max
  );
}

interface StyleBrowserProps {
  styles: StyleOut[];
  favorites: string[];
  selected: string[];
  onToggleFavorite: (key: string) => void;
  onToggleSelect: (key: string) => void;
  onPlay: (key: string) => void;
}

/**
 * Buscador de estilos: texto, categoría, modo y rango de BPM. Los favoritos van primero; la selección es múltiple
 * (una pista por estilo). Sin categoría de «mood»: se descartó en la 011 (su ficha está en WARNING).
 */
export function StyleBrowser({
  styles,
  favorites,
  selected,
  onToggleFavorite,
  onToggleSelect,
  onPlay,
}: StyleBrowserProps): React.JSX.Element {
  const [query, setQuery] = useState('');
  const [category, setCategory] = useState<string | null>(null);
  const [mode, setMode] = useState<Mode>('all');
  const [bpmMin, setBpmMin] = useState('30');
  const [bpmMax, setBpmMax] = useState('300');

  const categories = useMemo(() => [...new Set(styles.map((style) => style.category))].sort(), [styles]);
  const visible = useMemo(() => {
    const filters: Filters = { query, category, mode, min: Number(bpmMin) || 0, max: Number(bpmMax) || Infinity };
    const rank = (style: StyleOut) => (favorites.includes(style.key) ? 0 : 1);
    return styles.filter((style) => matches(style, filters)).sort((a, b) => rank(a) - rank(b));
  }, [styles, favorites, query, category, mode, bpmMin, bpmMax]);

  const modes: { value: Mode; text: string }[] = [
    { value: 'all', text: t('music.style.mode.all') },
    { value: 'major', text: t('music.style.mode.major') },
    { value: 'minor', text: t('music.style.mode.minor') },
  ];

  return (
    <UIStack gap="md">
      <UIField label={t('music.style.search')} value={query} onChange={(event) => setQuery(event.target.value)} />
      <UIStack gap="sm">
        <UIText variant="caption">{t('music.style.category')}</UIText>
        <UIStack direction="row" gap="sm" className="flex-wrap">
          {categories.map((name) => (
            <UIButton
              key={name}
              variant={category === name ? 'primary' : 'secondary'}
              aria-pressed={category === name}
              onClick={() => setCategory(category === name ? null : name)}
            >
              {label('music.category', name)}
            </UIButton>
          ))}
        </UIStack>
      </UIStack>
      <UIStack gap="sm">
        <UIText variant="caption">{t('music.style.mode')}</UIText>
        <UIStack direction="row" gap="sm">
          {modes.map((option) => (
            <UIButton
              key={option.value}
              variant={mode === option.value ? 'primary' : 'secondary'}
              aria-pressed={mode === option.value}
              onClick={() => setMode(option.value)}
            >
              {option.text}
            </UIButton>
          ))}
        </UIStack>
      </UIStack>
      <UIStack direction="row" gap="md">
        <UIField label={t('music.style.bpmMin')} type="number" value={bpmMin} onChange={(event) => setBpmMin(event.target.value)} />
        <UIField label={t('music.style.bpmMax')} type="number" value={bpmMax} onChange={(event) => setBpmMax(event.target.value)} />
      </UIStack>
      {visible.length === 0 ? (
        <UIText variant="caption">{t('music.style.empty')}</UIText>
      ) : (
        <UIStack gap="sm" direction="row" className="flex-wrap">
          {visible.map((style) => (
            <StyleCard
              key={style.key}
              style={style}
              favorite={favorites.includes(style.key)}
              selected={selected.includes(style.key)}
              onToggleFavorite={() => onToggleFavorite(style.key)}
              onToggleSelect={() => onToggleSelect(style.key)}
              onPlay={() => onPlay(style.key)}
            />
          ))}
        </UIStack>
      )}
    </UIStack>
  );
}

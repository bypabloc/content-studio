import type { components } from '@/shared/api/schema';
import { UIButton } from '@/shared/components/atoms/UIButton';
import { UIStack } from '@/shared/components/atoms/UIStack';
import { UIText } from '@/shared/components/atoms/UIText';
import { label, t } from '@/shared/i18n/t';

type StyleOut = components['schemas']['StyleOut'];

const PLAY = '▶';

interface StyleCardProps {
  style: StyleOut;
  favorite: boolean;
  selected: boolean;
  onToggleFavorite: () => void;
  onToggleSelect: () => void;
  /** Suena la muestra de 10 s del preset (solo si ya existe). */
  onPlay: () => void;
}

/** Un preset del buscador: elegirlo, marcarlo ★ y escuchar su muestra ▶ si la tiene (spec 011, D-5). */
export function StyleCard({
  style,
  favorite,
  selected,
  onToggleFavorite,
  onToggleSelect,
  onPlay,
}: StyleCardProps): React.JSX.Element {
  const name = label('music.style', style.key);
  return (
    <UIStack gap="xs" className="rounded-md border p-3" data-style={style.key}>
      <UIStack direction="row" gap="sm" align="center" justify="between">
        <UIButton variant={selected ? 'primary' : 'ghost'} aria-pressed={selected} onClick={onToggleSelect}>
          {name}
        </UIButton>
        <UIStack direction="row" gap="xs">
          <UIButton variant="ghost" aria-pressed={favorite} aria-label={t('music.style.favorite')} onClick={onToggleFavorite}>
            {favorite ? '★' : '☆'}
          </UIButton>
          {style.has_sample ? (
            <UIButton variant="ghost" aria-label={t('music.style.play', { style: name })} onClick={onPlay}>
              {PLAY}
            </UIButton>
          ) : null}
        </UIStack>
      </UIStack>
      <UIText variant="caption">{t('music.style.meta', { key: style.musical_key, bpm: style.bpm })}</UIText>
    </UIStack>
  );
}

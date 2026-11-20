import { useState } from 'react';
import { useApi } from '@/shared/api/context';
import { UIButton } from '@/shared/components/atoms/UIButton';
import { UICard } from '@/shared/components/atoms/UICard';
import { UICheckbox } from '@/shared/components/atoms/UICheckbox';
import { UIGrid } from '@/shared/components/atoms/UIGrid';
import { UIStack } from '@/shared/components/atoms/UIStack';
import { UIText } from '@/shared/components/atoms/UIText';
import { UIIconButton } from '@/shared/components/molecules/UIIconButton';
import { useSetting } from '@/shared/hooks/useSetting';
import { t } from '@/shared/i18n/t';
import { Player } from '@/shared/media/Player';
import { useMediaPeaks } from '@/shared/media/useMediaInfo';
import { type VoiceCard, useEnqueueVoiceBuild, useVoiceCatalog } from './useVoices';

/** El texto del estado de una voz: sin construir, parcial o aprobada. */
function stateText(state: VoiceCard['state']): string {
  switch (state) {
    case 'approved':
      return t('voices.catalog.state.approved');
    case 'partial':
      return t('voices.catalog.state.partial');
    default:
      return t('voices.catalog.state.not_built');
  }
}

/** La muestra de un estilo aprobado: su forma de onda y su reproductor. El server la sirve desde su carpeta de voces. */
function Sample({ path }: { path: string }): React.JSX.Element | null {
  const api = useApi();
  const peaks = useMediaPeaks(path);
  return peaks.data ? <Player src={api.fileUrl(path)} peaks={peaks.data.peaks} /> : null;
}

/** Una voz del catálogo: su ficha, su licencia, ★ favorita, sus muestras aprobadas y «Construir». */
function VoiceCardView({
  voice,
  favorite,
  onFavorite,
  onBuild,
}: {
  voice: VoiceCard;
  favorite: boolean;
  onFavorite: () => void;
  onBuild: () => void;
}): React.JSX.Element {
  return (
    <UICard>
      <UIStack gap="sm" className="flex-1 p-5">
        <UIStack direction="row" align="center" justify="between" gap="sm">
          <UIText variant="heading">{voice.id}</UIText>
          <UIIconButton
            icon="star"
            label={t('voices.catalog.favorite_of', { name: voice.id })}
            pressed={favorite}
            onClick={onFavorite}
          />
        </UIStack>
        <UIText variant="caption">{stateText(voice.state)}</UIText>
        {voice.license ? <UIText variant="caption">{t('voices.catalog.license', { license: voice.license })}</UIText> : null}
        {voice.description ? <UIText variant="body">{voice.description}</UIText> : null}
        {voice.styles.map((style) => (style.approved && style.path ? <Sample key={style.style} path={style.path} /> : null))}
        <UIButton
          variant="secondary"
          className="mt-auto"
          aria-label={t('voices.catalog.build_named', { name: voice.id })}
          onClick={onBuild}
        >
          {t('voices.catalog.build')}
        </UIButton>
      </UIStack>
    </UICard>
  );
}

/**
 * El catálogo de voces libres (spec 010, D-5 y AC-7): cada voz con su ficha, ★ favorita (AC-9), «Construir» por voz o
 * «Construir todas», y «Forzar» para rehacer las ya aprobadas. Lo que se construye va a la cola: su avance se ve ahí.
 */
export function CatalogPage(): React.JSX.Element | null {
  const catalog = useVoiceCatalog();
  const enqueue = useEnqueueVoiceBuild();
  const [favorites, setFavorites] = useSetting<string[]>('voices.favorites', []);
  const [force, setForce] = useState(false);
  // Sin catálogo no hay controles: así «Construir todas» no aparece antes de saber qué voces hay.
  if (!catalog.data) return null;
  const voices = catalog.data.voices;
  const build = (names: string[]) => enqueue.mutate({ voices: names, force });
  const toggle = (name: string) =>
    setFavorites(favorites.includes(name) ? favorites.filter((item) => item !== name) : [...favorites, name]);

  return (
    <UIStack gap="lg">
      <UIText variant="caption">{t('voices.catalog.intro')}</UIText>
      <UIStack direction="row" align="center" gap="md">
        <UIButton variant="primary" disabled={voices.length === 0} onClick={() => build(voices.map((voice) => voice.id))}>
          {t('voices.catalog.build_all')}
        </UIButton>
        <UICheckbox label={t('voices.catalog.force')} checked={force} onChange={setForce} />
      </UIStack>
      <UIGrid columns={2}>
        {voices.map((voice) => (
          <VoiceCardView
            key={voice.id}
            voice={voice}
            favorite={favorites.includes(voice.id)}
            onFavorite={() => toggle(voice.id)}
            onBuild={() => build([voice.id])}
          />
        ))}
      </UIGrid>
    </UIStack>
  );
}

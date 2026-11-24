import { UIButton } from '@/shared/components/atoms/UIButton';
import { UICard } from '@/shared/components/atoms/UICard';
import { UIProgress } from '@/shared/components/atoms/UIProgress';
import { UIStack } from '@/shared/components/atoms/UIStack';
import { UIText } from '@/shared/components/atoms/UIText';
import { UIIconButton } from '@/shared/components/molecules/UIIconButton';
import { t } from '@/shared/i18n/t';
import type { ProfileSummary } from './useVoices';

type Props = {
  profile: ProfileSummary;
  done: number;
  total: number;
  onOpen: () => void;
  onRename: () => void;
  onRemove: () => void;
};

/**
 * Un perfil en la lista: su nombre, su progreso sobre los estilos obligatorios (`done` de `total`) y sus acciones. Abrir va
 * con texto; renombrar y borrar, con ícono y su nombre accesible (spec 010, D-6).
 */
export function ProfileCard({ profile, done, total, onOpen, onRename, onRemove }: Props) {
  const id = `voice-${profile.id}`;
  const progress = t('voices.progress', { done, total });
  return (
    <UICard aria-labelledby={id}>
      <UIText variant="subtitle" id={id}>
        {profile.name}
      </UIText>
      {total > 0 ? (
        <UIStack gap="sm" className="mt-4">
          <UIProgress value={done / total} label={progress} />
          <UIText variant="caption">{progress}</UIText>
        </UIStack>
      ) : null}
      <UIStack direction="row" align="center" gap="sm" className="mt-4">
        <UIButton variant="secondary" onClick={onOpen}>
          {t('voices.open')}
        </UIButton>
        <UIIconButton icon="pencil" label={t('voices.rename')} onClick={onRename} />
        <UIIconButton icon="remove" label={t('voices.delete')} onClick={onRemove} />
      </UIStack>
    </UICard>
  );
}

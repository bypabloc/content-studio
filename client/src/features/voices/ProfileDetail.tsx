import { UIButton } from '@/shared/components/atoms/UIButton';
import { UIGrid } from '@/shared/components/atoms/UIGrid';
import { UIStack } from '@/shared/components/atoms/UIStack';
import { UIText } from '@/shared/components/atoms/UIText';
import { t } from '@/shared/i18n/t';
import { StyleCard } from './StyleCard';
import { useProfile } from './useVoices';

/**
 * La ficha de un perfil (spec 010, D-6): cada estilo del kit con su referencia elegida, reproducible, y sus tomas.
 * «Volver» regresa a la lista de perfiles; «Grabar» abre el asistente, e «Importar» el formulario de importar un tramo.
 */
export function ProfileDetail({
  slug,
  onBack,
  onRecord,
  onImport,
}: {
  slug: string;
  onBack: () => void;
  onRecord: () => void;
  onImport: () => void;
}) {
  const profile = useProfile(slug);
  return (
    <UIStack gap="lg">
      <UIButton variant="ghost" icon="chevron-left" className="self-start" onClick={onBack}>
        {t('voices.back')}
      </UIButton>
      {profile.data ? (
        <>
          <UIText variant="subtitle">{profile.data.name}</UIText>
          <UIStack direction="row" gap="sm">
            <UIButton icon="record" onClick={onRecord}>
              {t('voices.record.open')}
            </UIButton>
            <UIButton variant="secondary" icon="upload" onClick={onImport}>
              {t('voices.import.open')}
            </UIButton>
          </UIStack>
          <UIGrid columns={3}>
            {profile.data.styles.map((item) => (
              <StyleCard key={item.style} item={item} />
            ))}
          </UIGrid>
        </>
      ) : null}
    </UIStack>
  );
}

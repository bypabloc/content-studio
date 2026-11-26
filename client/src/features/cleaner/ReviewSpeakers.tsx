import { type SpeakerMap, UISpeakerChip } from '@/shared/components/molecules/UISpeakerLegend';
import { UIStack } from '@/shared/components/atoms/UIStack';
import { UIText } from '@/shared/components/atoms/UIText';
import { t } from '@/shared/i18n/t';

/** La palabra con el color de su hablante: un subrayado de 3 px (AC-8); sin hablante, sin subrayado. */
export function speakerUnderline(
  word: { speaker?: string | null },
  speakers: SpeakerMap | undefined,
): React.CSSProperties | undefined {
  const color = word.speaker ? speakers?.[word.speaker]?.color : undefined;
  return color ? { borderBottom: `3px solid ${color}` } : undefined; // i18n-ignore: estilo CSS, no es texto visible
}

/** La leyenda de solo lectura de los hablantes de la revisión: un chip por hablante con su color y su nombre. */
export function ReviewSpeakers({ speakers }: { speakers: SpeakerMap }): React.JSX.Element {
  return (
    <UIStack gap="xs">
      <UIText variant="caption">{t('cleaner.review.speakers')}</UIText>
      <UIStack direction="row" gap="md" className="flex-wrap">
        {Object.entries(speakers).map(([id, speaker]) => (
          <UISpeakerChip key={id} name={speaker.name} color={speaker.color} />
        ))}
      </UIStack>
    </UIStack>
  );
}

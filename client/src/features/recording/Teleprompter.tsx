import type { KitStyle } from '@/features/voices/useVoices';
import { UIEmphasis } from '@/shared/components/atoms/UIEmphasis';
import { UIStack } from '@/shared/components/atoms/UIStack';
import { UIText } from '@/shared/components/atoms/UIText';
import { label, t } from '@/shared/i18n/t';

// La negrita de la notación va entre dobles asteriscos: se pinta con UIEmphasis, y el resto de las marcas, tal cual.
function withBold(marked: string): React.ReactNode {
  return marked.split(/(\*\*[^*]+\*\*)/).map((part, index) =>
    part.length > 4 && part.startsWith('**') && part.endsWith('**') ? (
      <UIEmphasis key={index}>{part.slice(2, -2)}</UIEmphasis>
    ) : (
      part
    ),
  );
}

/**
 * El teleprompter de un estilo (spec 010, D-6): el guion marcado en letra grande, con su leyenda, la duración objetivo y el
 * ritmo. Lo que se dice en voz alta son las palabras; las marcas solo indican cómo decirlas.
 */
export function Teleprompter({ style, step, total }: { style: KitStyle; step: number; total: number }): React.JSX.Element {
  return (
    <UIStack gap="md">
      <UIText variant="heading">{label('narration.style', style.style)}</UIText>
      <UIText variant="caption">{t('voices.record.step', { n: step, total })}</UIText>
      {style.optional ? <UIText variant="caption">{t('voices.record.optional')}</UIText> : null}
      <UIText variant="display">{withBold(style.marked)}</UIText>
      <UIText variant="caption">{t('voices.record.notation')}</UIText>
      <UIStack direction="row" gap="md">
        <UIText variant="caption">{t('voices.record.duration', { min: style.duration.min, max: style.duration.max })}</UIText>
        {style.ppm !== null ? <UIText variant="caption">{t('voices.record.ppm', { ppm: style.ppm })}</UIText> : null}
      </UIStack>
    </UIStack>
  );
}

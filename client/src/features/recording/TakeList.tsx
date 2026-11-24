import { UIStack } from '@/shared/components/atoms/UIStack';
import { UIText } from '@/shared/components/atoms/UIText';
import { t } from '@/shared/i18n/t';
import { TakeRow } from './TakeRow';
import { useStyleTakes } from './useTakes';

/** Las tomas de un estilo, la más nueva primero: cada una con su veredicto, para reproducirla o elegirla (spec 010, D-6). */
export function TakeList({ slug, style }: { slug: string; style: string }): React.JSX.Element {
  const takes = useStyleTakes(slug, style);
  const numbers = [...(takes.data?.takes ?? [])].sort((a, b) => b - a);
  if (takes.isSuccess && numbers.length === 0) {
    return <UIText variant="caption">{t('voices.takes.empty')}</UIText>;
  }
  return (
    <UIStack gap="md">
      {numbers.map((take) => (
        <TakeRow key={take} slug={slug} style={style} take={take} />
      ))}
    </UIStack>
  );
}

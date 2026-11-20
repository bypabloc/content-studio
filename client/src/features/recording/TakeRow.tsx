import { useState } from 'react';
import { useApi } from '@/shared/api/context';
import { UIButton } from '@/shared/components/atoms/UIButton';
import { UICard } from '@/shared/components/atoms/UICard';
import { UIStack } from '@/shared/components/atoms/UIStack';
import { UIText } from '@/shared/components/atoms/UIText';
import { UIConfirmDialog } from '@/shared/components/organisms/UIConfirmDialog';
import { t } from '@/shared/i18n/t';
import { Player } from '@/shared/media/Player';
import { useMediaPeaks } from '@/shared/media/useMediaInfo';
import { type Check, useChooseTake, useDeleteTake, useTakeDetail } from './useTakes';

/** El texto de una razón o una nota del chequeo, en el idioma activo. Las claves van escritas completas para el gate de i18n. */
function checkText(code: string): string {
  switch (code) {
    case 'too_long':
      return t('voice.check.too_long');
    case 'too_short':
      return t('voice.check.too_short');
    case 'peak_high':
      return t('voice.check.peak_high');
    case 'peak_low':
      return t('voice.check.peak_low');
    case 'edges':
      return t('voice.check.edges');
    case 'pause':
      return t('voice.check.pause');
    case 'noise':
      return t('voice.check.noise');
    case 'text':
      return t('voice.check.text');
    case 'whisper_missing':
      return t('voice.check.whisper_missing');
    case 'resampled':
      return t('voice.check.resampled');
    default:
      return code;
  }
}

function verdictText(check: Check | null | undefined): string {
  if (!check) return t('voices.take.pending');
  return check.verdict === 'ok' ? t('voices.take.ok') : t('voices.take.retake');
}

/**
 * Una toma de un estilo (spec 010, D-6): su veredicto y, si hay que repetirla, por qué. Se reproduce con su forma de onda
 * y se puede elegir como referencia.
 */
export function TakeRow({ slug, style, take }: { slug: string; style: string; take: number }): React.JSX.Element {
  const api = useApi();
  const detail = useTakeDetail(slug, style, take);
  const choose = useChooseTake(slug, style);
  const remove = useDeleteTake(slug, style);
  const [confirming, setConfirming] = useState(false);
  const path = detail.data?.path ?? null;
  const peaks = useMediaPeaks(path ?? '');
  const check = detail.data?.check;
  const id = `take-${style}-${take}`;
  return (
    <UICard aria-labelledby={id}>
      <UIText variant="heading" id={id}>
        {t('voices.take.title', { n: take })}
      </UIText>
      <UIStack gap="sm" className="mt-2">
        <UIText variant="caption">{verdictText(check)}</UIText>
        {check
          ? [...check.reasons, ...check.notes].map((code) => (
              <UIText key={code} variant="caption">
                {checkText(code)}
              </UIText>
            ))
          : null}
      </UIStack>
      {path && peaks.data ? (
        <UIStack className="mt-4">
          <Player src={api.fileUrl(path)} peaks={peaks.data.peaks} />
        </UIStack>
      ) : null}
      <UIStack direction="row" className="mt-4" gap="sm">
        <UIButton variant="secondary" onClick={() => choose.mutate(take)}>
          {t('action.choose')}
        </UIButton>
        <UIButton variant="ghost" icon="trash-2" onClick={() => setConfirming(true)}>
          {t('voices.take.delete')}
        </UIButton>
      </UIStack>
      <UIConfirmDialog
        open={confirming}
        onOpenChange={setConfirming}
        title={t('voices.take.delete.title', { n: take })}
        description={t('voices.take.delete.description')}
        confirmLabel={t('voices.delete.confirm')}
        cancelLabel={t('action.cancel')}
        destructive
        pending={remove.isPending}
        onConfirm={() => {
          setConfirming(false);
          remove.mutate(take);
        }}
      />
    </UICard>
  );
}

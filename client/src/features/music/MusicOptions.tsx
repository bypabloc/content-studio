import { useState } from 'react';

import { UIButton } from '@/shared/components/atoms/UIButton';
import { UIStack } from '@/shared/components/atoms/UIStack';
import { UIField } from '@/shared/components/molecules/UIField';
import { t } from '@/shared/i18n/t';

export const MAX_VARIANTS = 6;
export const MAX_RETRIES = 3;

interface MusicOptionsProps {
  variants: number;
  onVariants: (variants: number) => void;
  noLm: boolean;
  onNoLm: (noLm: boolean) => void;
  evaluate: boolean;
  onEvaluate: (evaluate: boolean) => void;
  retries: number;
  onRetries: (retries: number) => void;
}

/** Un entero dentro de un rango, o null si el texto no lo es todavía (mientras se escribe). */
function integerIn(text: string, min: number, max: number): number | null {
  const value = Number(text);
  return Number.isInteger(value) && value >= min && value <= max ? value : null;
}

/**
 * «Avanzado» de Música (spec 011, D-6): variantes (1–6), sin planificador LM, evaluar la voz y reintentos.
 * Los campos guardan lo escrito y solo avisan cuando el número es válido.
 */
export function MusicOptions({
  variants,
  onVariants,
  noLm,
  onNoLm,
  evaluate,
  onEvaluate,
  retries,
  onRetries,
}: MusicOptionsProps): React.JSX.Element {
  const [open, setOpen] = useState(false);
  const [variantsDraft, setVariantsDraft] = useState(String(variants));
  const [retriesDraft, setRetriesDraft] = useState(String(retries));
  return (
    <UIStack gap="sm">
      <UIButton variant="ghost" aria-expanded={open} onClick={() => setOpen((current) => !current)}>
        {t('music.advanced')}
      </UIButton>
      {open ? (
        <UIStack gap="md">
          <UIField
            label={t('music.options.variants')}
            type="number"
            min={1}
            max={MAX_VARIANTS}
            value={variantsDraft}
            onChange={(event) => {
              setVariantsDraft(event.target.value);
              const next = integerIn(event.target.value, 1, MAX_VARIANTS);
              if (next !== null) onVariants(next);
            }}
          />
          <UIButton variant="secondary" aria-pressed={noLm} onClick={() => onNoLm(!noLm)}>
            {t('music.options.noLm')}
          </UIButton>
          <UIButton variant="secondary" aria-pressed={evaluate} onClick={() => onEvaluate(!evaluate)}>
            {t('music.options.evaluate')}
          </UIButton>
          <UIField
            label={t('music.options.retries')}
            type="number"
            min={0}
            max={MAX_RETRIES}
            value={retriesDraft}
            onChange={(event) => {
              setRetriesDraft(event.target.value);
              const next = integerIn(event.target.value, 0, MAX_RETRIES);
              if (next !== null) onRetries(next);
            }}
          />
        </UIStack>
      ) : null}
    </UIStack>
  );
}

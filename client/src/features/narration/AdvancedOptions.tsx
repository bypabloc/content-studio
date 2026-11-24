import { useState } from 'react';
import { UICheckbox } from '@/shared/components/atoms/UICheckbox';
import { UIStack } from '@/shared/components/atoms/UIStack';
import { UIField } from '@/shared/components/molecules/UIField';
import { UISelect } from '@/shared/components/molecules/UISelect';
import { useSetting } from '@/shared/hooks/useSetting';
import { t } from '@/shared/i18n/t';

/** Lo avanzado de la narración: masterización, semilla, lote, evaluación y reintentos. Cada valor se recuerda. */
export function AdvancedOptions({ supportsBatch }: { supportsBatch: boolean }) {
  const [master, setMaster] = useSetting<string>('narration.master', 'voice');
  const [lufs, setLufs] = useSetting<number>('narration.lufs', -16);
  // Mientras se escribe, el texto va aparte: borrar el campo o un signo menos suelto no es un número y no se guarda.
  const [lufsDraft, setLufsDraft] = useState<string | null>(null);
  const [seed, setSeed] = useSetting<number | null>('narration.seed', null);
  const [batch, setBatch] = useSetting<number | null>('narration.batch', null);
  const [evaluate, setEvaluate] = useSetting<boolean>('narration.evaluate', false);
  const [retries, setRetries] = useSetting<number>('narration.retries', 0);
  const numberOrNull = (text: string) => (text === '' ? null : Number(text));

  return (
    <UIStack gap="md" className="text-sm">
      <UISelect
        label={t('narration.advanced.master')}
        options={[
          { value: 'voice', label: t('narration.master.voice') },
          { value: 'no', label: t('narration.master.no') },
        ]}
        value={master}
        onChange={setMaster}
      />
      <UIField
        type="number"
        label={t('narration.advanced.lufs')}
        value={lufsDraft ?? String(lufs)}
        onChange={(event) => {
          setLufsDraft(event.target.value);
          const next = Number(event.target.value);
          if (event.target.value !== '' && Number.isFinite(next)) setLufs(next);
        }}
        onBlur={() => setLufsDraft(null)}
      />
      <UIField
        type="number"
        label={t('narration.advanced.seed')}
        value={seed ?? ''}
        onChange={(event) => setSeed(numberOrNull(event.target.value))}
      />
      {supportsBatch && (
        <UIField
          type="number"
          label={t('narration.advanced.batch')}
          value={batch ?? ''}
          onChange={(event) => setBatch(numberOrNull(event.target.value))}
        />
      )}
      <UICheckbox label={t('narration.advanced.evaluate')} checked={evaluate} onChange={setEvaluate} />
      <UIField
        type="number"
        label={t('narration.advanced.retries')}
        min={0}
        max={3}
        value={retries}
        onChange={(event) => setRetries(Number(event.target.value))}
      />
    </UIStack>
  );
}

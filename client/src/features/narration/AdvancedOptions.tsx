import { useSetting } from '@/shared/hooks/useSetting';
import { t } from '@/shared/i18n/t';

/** Lo avanzado de la narración: masterización, semilla, lote, evaluación y reintentos. Cada valor se recuerda. */
export function AdvancedOptions({ supportsBatch }: { supportsBatch: boolean }) {
  const [master, setMaster] = useSetting<string>('narration.master', 'voice');
  const [lufs, setLufs] = useSetting<number>('narration.lufs', -16);
  const [seed, setSeed] = useSetting<number | null>('narration.seed', null);
  const [batch, setBatch] = useSetting<number | null>('narration.batch', null);
  const [evaluate, setEvaluate] = useSetting<boolean>('narration.evaluate', false);
  const [retries, setRetries] = useSetting<number>('narration.retries', 0);
  const numberOrNull = (text: string) => (text === '' ? null : Number(text));

  return (
    <div className="flex flex-col gap-3 text-sm">
      <label className="flex items-center justify-between gap-3">
        {t('narration.advanced.master')}
        <select
          aria-label={t('narration.advanced.master')}
          value={master}
          onChange={(event) => setMaster(event.target.value)}
          className="rounded-md border border-input bg-transparent px-2 py-1.5"
        >
          <option value="voice">{t('narration.master.voice')}</option>
          <option value="no">{t('narration.master.no')}</option>
        </select>
      </label>
      <label className="flex items-center justify-between gap-3">
        {t('narration.advanced.lufs')}
        <input
          type="number"
          aria-label={t('narration.advanced.lufs')}
          value={lufs}
          onChange={(event) => setLufs(Number(event.target.value))}
          className="w-24 rounded-md border border-input bg-transparent px-2 py-1.5"
        />
      </label>
      <label className="flex items-center justify-between gap-3">
        {t('narration.advanced.seed')}
        <input
          type="number"
          aria-label={t('narration.advanced.seed')}
          value={seed ?? ''}
          onChange={(event) => setSeed(numberOrNull(event.target.value))}
          className="w-24 rounded-md border border-input bg-transparent px-2 py-1.5"
        />
      </label>
      {supportsBatch && (
        <label className="flex items-center justify-between gap-3">
          {t('narration.advanced.batch')}
          <input
            type="number"
            aria-label={t('narration.advanced.batch')}
            value={batch ?? ''}
            onChange={(event) => setBatch(numberOrNull(event.target.value))}
            className="w-24 rounded-md border border-input bg-transparent px-2 py-1.5"
          />
        </label>
      )}
      <label className="flex items-center justify-between gap-3">
        {t('narration.advanced.evaluate')}
        <input
          type="checkbox"
          checked={evaluate}
          onChange={(event) => setEvaluate(event.target.checked)}
        />
      </label>
      <label className="flex items-center justify-between gap-3">
        {t('narration.advanced.retries')}
        <input
          type="number"
          aria-label={t('narration.advanced.retries')}
          min={0}
          max={3}
          value={retries}
          onChange={(event) => setRetries(Number(event.target.value))}
          className="w-24 rounded-md border border-input bg-transparent px-2 py-1.5"
        />
      </label>
    </div>
  );
}

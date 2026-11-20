import { open } from '@tauri-apps/plugin-dialog';
import { useState } from 'react';
import { useKit } from '@/features/voices/useVoices';
import { UIButton } from '@/shared/components/atoms/UIButton';
import { UICheckbox } from '@/shared/components/atoms/UICheckbox';
import { UIStack } from '@/shared/components/atoms/UIStack';
import { UIText } from '@/shared/components/atoms/UIText';
import { UIField } from '@/shared/components/molecules/UIField';
import { UISelect } from '@/shared/components/molecules/UISelect';
import { label, t } from '@/shared/i18n/t';
import { useImportSpan } from './useTakes';

// cspell:ignore flac mkv webm
// Lo que deja elegir el diálogo: audio y video comunes. Lo lee ffmpeg en el server; la lista solo filtra.
const MEDIA_EXTENSIONS = ['wav', 'mp3', 'flac', 'ogg', 'm4a', 'mp4', 'mov', 'mkv', 'webm'];
// El tramo que se importa: de 8 a 12 segundos (spec 010, D-4 y AC-6). Es el mismo límite que valida el server.
const MIN_SPAN = 8;
const MAX_SPAN = 12;

/**
 * El formulario de importar una referencia (spec 010, D-4): se elige el archivo con el diálogo del sistema, el estilo, el
 * tramo de 8 a 12 s y el permiso del dueño. El server extrae el tramo como toma y encola su chequeo; al terminar se vuelve
 * a la ficha, donde la toma aparece en su estilo.
 */
export function ImportReference({ slug, onDone }: { slug: string; onDone: () => void }): React.JSX.Element {
  const kit = useKit();
  const importSpan = useImportSpan(slug);
  const [path, setPath] = useState<string | null>(null);
  const [style, setStyle] = useState('');
  const [start, setStart] = useState('');
  const [end, setEnd] = useState('');
  const [consent, setConsent] = useState(false);
  const filled = start !== '' && end !== '';
  const span = Number(end) - Number(start);
  const spanOk = filled && span >= MIN_SPAN && span <= MAX_SPAN;
  const ready = path !== null && style !== '' && spanOk && consent;

  const pick = async () => {
    try {
      const chosen = await open({ multiple: false, filters: [{ name: t('voices.import.media'), extensions: MEDIA_EXTENSIONS }] });
      if (typeof chosen === 'string') setPath(chosen);
    } catch {
      // Sin la ventana de Tauri no hay diálogo: no se elige nada y el formulario sigue igual.
    }
  };

  const submit = () => {
    if (!ready || path === null) return;
    importSpan.mutate({ path, start: Number(start), end: Number(end), style }, { onSuccess: onDone });
  };

  const name = path === null ? t('voices.import.no_file') : (path.split(/[\\/]/).pop() ?? path);
  const spanError = filled && !spanOk ? t('error.invalid_span', { low: MIN_SPAN, high: MAX_SPAN }) : undefined;

  return (
    <UIStack gap="lg">
      <UIButton variant="ghost" icon="chevron-left" className="self-start" onClick={onDone}>
        {t('voices.import.back')}
      </UIButton>
      <UIText variant="subtitle">{t('voices.import.title')}</UIText>
      <UIText variant="caption">{t('voices.import.hint')}</UIText>
      <UIStack direction="row" align="center" gap="md">
        <UIButton variant="secondary" icon="upload" onClick={() => void pick()}>
          {t('voices.import.choose')}
        </UIButton>
        <UIText variant="caption">{name}</UIText>
      </UIStack>
      <UISelect
        label={t('voices.import.style')}
        emptyOption={t('voices.import.style_empty')}
        options={(kit.data?.styles ?? []).map((item) => ({ value: item.style, label: label('narration.style', item.style) }))}
        value={style}
        onChange={setStyle}
      />
      <UIStack direction="row" gap="md">
        <UIField
          type="number"
          label={t('voices.import.start')}
          unit="s"
          min={0}
          step={0.1}
          value={start}
          onChange={(event) => setStart(event.target.value)}
        />
        <UIField
          type="number"
          label={t('voices.import.end')}
          unit="s"
          min={0}
          step={0.1}
          value={end}
          error={spanError}
          onChange={(event) => setEnd(event.target.value)}
        />
      </UIStack>
      <UICheckbox label={t('voice.consent.import')} checked={consent} onChange={setConsent} />
      {importSpan.error ? <UIText variant="caption">{importSpan.error.message}</UIText> : null}
      <UIButton variant="primary" icon="upload" disabled={!ready || importSpan.isPending} onClick={submit}>
        {t('voices.import.submit')}
      </UIButton>
    </UIStack>
  );
}

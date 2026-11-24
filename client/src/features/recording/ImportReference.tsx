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
import { SpanPicker } from './SpanPicker';
import { MAX_SPAN, MIN_SPAN } from './span';
import { useImportSpan, useSourcePeaks } from './useTakes';

// cspell:ignore flac mkv webm
// Lo que deja elegir el diálogo: audio y video comunes. Lo lee ffmpeg en el server; la lista solo filtra.
const MEDIA_EXTENSIONS = ['wav', 'mp3', 'flac', 'ogg', 'm4a', 'mp4', 'mov', 'mkv', 'webm'];
// El tramo que se propone al elegir el archivo: de 0 a 10 s, o hasta el final si el archivo es más corto.
const DEFAULT_END = 10;
// Los segundos del tramo con dos decimales, como los escribe el campo.
const seconds = (value: number): string => String(Math.round(value * 100) / 100);

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
  const peaks = useSourcePeaks(path ?? '');
  // Sin picos (todavía no llegan, o la respuesta no los trae) no hay onda que dibujar.
  const source = Array.isArray(peaks.data?.peaks) ? peaks.data : undefined;
  // El tramo que se ve: lo que el usuario escribió o, si todavía no escribió nada, el que propone la onda (0 a 10 s).
  const shownStart = start !== '' || !source ? start : '0';
  const shownEnd = end !== '' || !source ? end : seconds(Math.min(DEFAULT_END, source.duration));
  const filled = shownStart !== '' && shownEnd !== '';
  const span = Number(shownEnd) - Number(shownStart);
  const spanOk = filled && span >= MIN_SPAN && span <= MAX_SPAN;
  const ready = path !== null && style !== '' && spanOk && consent;

  const pick = async () => {
    try {
      const chosen = await open({ multiple: false, filters: [{ name: t('voices.import.media'), extensions: MEDIA_EXTENSIONS }] });
      if (typeof chosen === 'string') {
        // Un archivo distinto empieza con el tramo vacío: el de antes pudo no caber en el nuevo.
        if (chosen !== path) {
          setStart('');
          setEnd('');
        }
        setPath(chosen);
      }
    } catch {
      // Sin la ventana de Tauri no hay diálogo: no se elige nada y el formulario sigue igual.
    }
  };

  const submit = () => {
    if (!ready || path === null) return;
    importSpan.mutate({ path, start: Number(shownStart), end: Number(shownEnd), style }, { onSuccess: onDone });
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
      {source ? (
        <SpanPicker
          peaks={source.peaks}
          duration={source.duration}
          start={Number(shownStart) || 0}
          end={Number(shownEnd) || 0}
          onChange={(from, to) => {
            setStart(seconds(from));
            setEnd(seconds(to));
          }}
        />
      ) : null}
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
          value={shownStart}
          onChange={(event) => setStart(event.target.value)}
        />
        <UIField
          type="number"
          label={t('voices.import.end')}
          unit="s"
          min={0}
          step={0.1}
          value={shownEnd}
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

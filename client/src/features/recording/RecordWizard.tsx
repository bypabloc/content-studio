import { useEffect, useRef, useState } from 'react';
import { useKit } from '@/features/voices/useVoices';
import { UIButton } from '@/shared/components/atoms/UIButton';
import { UIStack } from '@/shared/components/atoms/UIStack';
import { UIText } from '@/shared/components/atoms/UIText';
import { t } from '@/shared/i18n/t';
import { RecordControls } from './RecordControls';
import { TakeList } from './TakeList';
import { Teleprompter } from './Teleprompter';
import { useRecorder } from './capture/useRecorder';
import { useRoomTest } from './useRoomTest';
import { useUploadTake } from './useTakes';

// idle: libre; starting: el micrófono se abre; recording: se graba; uploading: la toma se sube.
type Phase = 'idle' | 'starting' | 'recording' | 'uploading';

// Un botón, un campo o un enlace ya usan la tecla de espacio: el asistente no se la quita.
function keepsSpace(target: EventTarget | null): boolean {
  return (
    target instanceof HTMLElement &&
    (target.isContentEditable || ['INPUT', 'TEXTAREA', 'SELECT', 'BUTTON', 'A'].includes(target.tagName)) // i18n-ignore: nombres de etiquetas HTML, no texto visible
  );
}

/**
 * El asistente de grabación de un perfil (spec 010, D-6): recorre el kit en orden, con el teleprompter, el medidor de nivel
 * y el reloj. Al parar, la toma se sube sola y su veredicto aparece con las demás tomas del estilo. Espacio graba y para.
 * «Volver a la ficha» queda bloqueado mientras hay una toma en curso, para no perderla.
 */
export function RecordWizard({ slug, onDone }: { slug: string; onDone: () => void }): React.JSX.Element | null {
  const kit = useKit();
  const recorder = useRecorder();
  const room = useRoomTest(recorder);
  const [index, setIndex] = useState(0);
  const [phase, setPhase] = useState<Phase>('idle');
  // La fase también va en una referencia: el atajo de teclado la lee sin esperar a que React vuelva a pintar.
  const phaseRef = useRef<Phase>('idle');
  const [elapsed, setElapsed] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [finished, setFinished] = useState(false);
  const styles = kit.data?.styles ?? [];
  const current = styles[index];
  const upload = useUploadTake(slug, current?.style ?? '');
  const locked = phase === 'starting' || phase === 'uploading' || room.running;
  const busy = phase !== 'idle' || room.running;

  const move = (next: Phase) => {
    phaseRef.current = next;
    setPhase(next);
  };

  const start = async () => {
    setError(null);
    move('starting');
    try {
      await recorder.start();
      setElapsed(0);
      move('recording');
    } catch {
      move('idle');
      setError(t('voices.record.error'));
    }
  };

  const stopAndUpload = async () => {
    move('uploading');
    try {
      const wav = await recorder.stop();
      if (wav) await upload.mutateAsync(wav);
    } catch {
      setError(t('voices.record.upload_error'));
    }
    move('idle');
  };

  // Grabar y parar cambian de sentido solo en su fase: mientras el micrófono abre o la toma sube, no hacen nada.
  const toggle = () => {
    if (!current || finished || room.running) return;
    if (phaseRef.current === 'recording') void stopAndUpload();
    else if (phaseRef.current === 'idle') void start();
  };

  // El atajo se registra en la fase de captura: así el reproductor de una toma no se come la tecla de espacio.
  const toggleRef = useRef(toggle);
  useEffect(() => {
    toggleRef.current = toggle;
  });
  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if (event.key !== ' ' || keepsSpace(event.target)) return;
      event.preventDefault();
      event.stopImmediatePropagation();
      toggleRef.current();
    };
    window.addEventListener('keydown', onKey, true);
    return () => window.removeEventListener('keydown', onKey, true);
  }, []);

  // El reloj de la grabación, cada décima de segundo.
  useEffect(() => {
    if (phase !== 'recording') return undefined;
    const started = Date.now();
    const clock = setInterval(() => setElapsed((Date.now() - started) / 1000), 100);
    return () => clearInterval(clock);
  }, [phase]);

  if (!current) return null;

  const next = () => {
    setError(null);
    if (index + 1 < styles.length) setIndex(index + 1);
    else setFinished(true);
  };
  const db = room.result?.db.toFixed(1) ?? '';

  return (
    <UIStack gap="lg">
      <UIButton variant="ghost" icon="chevron-left" className="self-start" disabled={busy} onClick={onDone}>
        {t('voices.record.back')}
      </UIButton>
      {finished ? (
        <UIText variant="subtitle">{t('voices.record.finished')}</UIText>
      ) : (
        <>
          <Teleprompter style={current} step={index + 1} total={styles.length} />
          <RecordControls
            recording={phase === 'recording'}
            levels={recorder.levels}
            elapsed={elapsed}
            target={current.duration}
            disabled={locked}
            onToggle={toggle}
          />
          {error ? <UIText variant="caption">{error}</UIText> : null}
          <UIStack direction="row" align="center" gap="sm">
            <UIButton variant="secondary" disabled={busy} onClick={toggle}>
              {t('voices.record.repeat')}
            </UIButton>
            <UIButton variant="primary" disabled={busy} onClick={next}>
              {t('voices.record.next')}
            </UIButton>
            <UIButton variant="ghost" disabled={busy} onClick={room.run}>
              {t('voices.room.start')}
            </UIButton>
          </UIStack>
          {room.running ? <UIText variant="caption">{t('voices.room.running')}</UIText> : null}
          {room.failed ? <UIText variant="caption">{t('voices.record.error')}</UIText> : null}
          {room.result ? (
            <UIText variant="caption">
              {room.result.noisy ? t('voices.room.noisy', { db }) : t('voices.room.quiet', { db })}
            </UIText>
          ) : null}
          <TakeList slug={slug} style={current.style} />
        </>
      )}
    </UIStack>
  );
}

import { useState } from 'react';

import { UIButton } from '@/shared/components/atoms/UIButton';
import { UIStack } from '@/shared/components/atoms/UIStack';
import { UIText } from '@/shared/components/atoms/UIText';
import { UIField } from '@/shared/components/molecules/UIField';
import { t } from '@/shared/i18n/t';

import { formatClock, parseClock } from './parseClock';

/** Una narración terminada (o su duración) con la que se puede igualar la pista (spec 011, D-4). */
export interface MatchSource {
  id: string;
  label: string;
  starred: boolean;
  duration: number;
}

export interface DurationFieldProps {
  /** Duración elegida, en segundos. */
  value: number;
  /** Máximo del motor elegido, en segundos (HeartMuLa 240, ACE-Step 600). */
  max: number;
  /** Cola de la igualación, en segundos (`music.match_tail`, 2 por defecto). */
  tail: number;
  /** Narraciones terminadas, ★ primero. */
  matchSources: MatchSource[];
  onChange: (seconds: number) => void;
  onTailChange: (seconds: number) => void;
  /** Abre el diálogo de archivo y devuelve la duración del elegido, o null si se cancela. */
  pickMediaDuration: () => Promise<number | null>;
}

const PRESETS = [15, 30, 60, 90, 180];

/** Un preset de 180 s se lee en minutos; los demás, en segundos. */
function presetLabel(seconds: number): string {
  return seconds >= 180
    ? t('music.duration.preset.minutes', { n: seconds / 60 })
    : t('music.duration.preset.seconds', { n: seconds });
}

/** Décimas exactas: 47.3 + 2 da 49.3 y no 49.300000000000004. */
function tenths(seconds: number): number {
  return Math.round(seconds * 10) / 10;
}

/** Campo de duración mm:ss con presets, el máximo del motor y «Igualar a…» (una narración o un archivo). */
export function DurationField({
  value,
  max,
  tail,
  matchSources,
  onChange,
  onTailChange,
  pickMediaDuration,
}: DurationFieldProps): React.JSX.Element {
  const [draft, setDraft] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [open, setOpen] = useState(false);
  const [tailDraft, setTailDraft] = useState(String(tail));

  function apply(seconds: number): void {
    if (seconds > max) {
      setError(t('error.duration_over_max', { max }));
      return;
    }
    setError(null);
    setDraft(null);
    onChange(seconds);
  }

  function commit(text: string): void {
    const seconds = parseClock(text);
    if (seconds === null) {
      setError(t('music.duration.invalid'));
      return;
    }
    apply(seconds);
  }

  function matchTo(base: number): void {
    apply(tenths(base + (Number.isFinite(Number(tailDraft)) ? Number(tailDraft) : 0)));
  }

  async function matchFile(): Promise<void> {
    const seconds = await pickMediaDuration();
    if (seconds !== null) matchTo(seconds);
  }

  return (
    <UIStack gap="md">
      <UIField
        label={t('music.duration.label')}
        value={draft ?? formatClock(value)}
        onChange={(event) => setDraft(event.target.value)}
        onFocus={(event) => event.currentTarget.select()}
        onBlur={(event) => commit(event.currentTarget.value)}
        onKeyDown={(event) => {
          if (event.key === 'Enter') commit(event.currentTarget.value);
        }}
        error={error ?? undefined}
        inputMode="decimal"
      />
      <UIStack direction="row" gap="sm" className="flex-wrap">
        {PRESETS.map((seconds) => (
          <UIButton
            key={seconds}
            variant="secondary"
            disabled={seconds > max}
            onClick={() => apply(seconds)}
          >
            {presetLabel(seconds)}
          </UIButton>
        ))}
      </UIStack>
      <UIStack gap="sm">
        <UIButton variant="secondary" aria-expanded={open} onClick={() => setOpen((current) => !current)}>
          {t('music.duration.match')}
        </UIButton>
        {open ? (
          <UIStack gap="sm" className="rounded-md border p-3">
            {matchSources.length === 0 ? (
              <UIText variant="caption">{t('music.duration.noSources')}</UIText>
            ) : (
              matchSources.map((source) => (
                <UIButton key={source.id} variant="ghost" onClick={() => matchTo(source.duration)}>
                  {`${source.starred ? '★ ' : ''}${source.label}`}
                </UIButton>
              ))
            )}
            <UIButton variant="ghost" onClick={() => void matchFile()}>
              {t('music.duration.matchFile')}
            </UIButton>
            <UIField
              label={t('music.duration.matchTail')}
              type="number"
              min={0}
              value={tailDraft}
              onChange={(event) => {
                setTailDraft(event.target.value);
                if (Number.isFinite(Number(event.target.value))) onTailChange(Number(event.target.value));
              }}
            />
          </UIStack>
        ) : null}
      </UIStack>
    </UIStack>
  );
}

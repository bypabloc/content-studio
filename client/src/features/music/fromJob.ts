import type { SourceJob } from '@/shared/hooks/useFromJob';

/** Lo que «Editar y repetir» (spec 020, AC-7) deja listo en Música a partir de los parámetros de un trabajo `music`. */
export interface MusicDraft {
  styles: string[];
  free: { caption: string; key: string | null; bpm: number | null; timeSignature: string } | null;
  duration: number | null;
  variants: number | null;
  noLm: boolean | null;
  evaluate: boolean | null;
  retries: number | null;
}

const num = (value: unknown) => (typeof value === 'number' ? value : null);
const bool = (value: unknown) => (typeof value === 'boolean' ? value : null);

/** Los estilos del trabajo (o su texto libre, si trae tonalidad, BPM o compás), la duración y las opciones avanzadas. */
export function musicDraft(job: SourceJob): MusicDraft {
  const p = job.params;
  const styles = Array.isArray(p.style) ? p.style.filter((style): style is string => typeof style === 'string') : [];
  const isFree = p.key !== undefined || p.bpm !== undefined || p.time_signature !== undefined;
  return {
    styles: isFree ? [] : styles,
    free: isFree
      ? {
          caption: styles[0] ?? '',
          key: typeof p.key === 'string' ? p.key : null,
          bpm: num(p.bpm),
          timeSignature: typeof p.time_signature === 'string' ? p.time_signature : '4',
        }
      : null,
    duration: num(p.duration),
    variants: num(p.variants),
    noLm: bool(p.no_lm),
    evaluate: bool(p.evaluate),
    retries: num(p.retries),
  };
}

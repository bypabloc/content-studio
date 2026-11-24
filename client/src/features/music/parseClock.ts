/**
 * Reloj de la duración (spec 011, D-4): `mm:ss`, `m:ss`, `ss` o con una décima (`00:49.3`) ↔ segundos.
 * La aritmética va en décimas enteras para que 49.3 no salga como 49.300000000000004.
 */

const CLOCK = /^(?:(\d+):)?(\d+)(?:\.(\d))?$/;

/** Segundos del texto, o null si no es un reloj válido (con minutos, los segundos son menores que 60). */
export function parseClock(text: string): number | null {
  const match = CLOCK.exec(text.trim());
  if (!match) return null;
  const [, minutes, seconds, tenth] = match;
  if (minutes !== undefined && Number(seconds) >= 60) return null;
  const whole = (minutes !== undefined ? Number(minutes) * 60 : 0) + Number(seconds);
  return (whole * 10 + Number(tenth ?? 0)) / 10;
}

/** Texto `mm:ss.d` de unos segundos, redondeados a la décima. */
export function formatClock(seconds: number): string {
  const tenths = Math.round(seconds * 10);
  const minutes = Math.floor(tenths / 600);
  const rest = tenths % 600;
  return `${String(minutes).padStart(2, '0')}:${String(Math.floor(rest / 10)).padStart(2, '0')}.${rest % 10}`;
}

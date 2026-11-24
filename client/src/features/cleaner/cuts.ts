/** Un corte en segundos del original (spec 013, D-3). `edited` marca lo que se movió o activó a mano: /plan no lo toca. */
export interface Cut {
  start: number;
  end: number;
  enabled: boolean;
  edited?: boolean;
}

/** Lo que queda del original: la duración menos los cortes activos, cada uno acotado a la duración. */
export function keepDuration(duration: number, cuts: Cut[]): number {
  const removed = cuts
    .filter((cut) => cut.enabled)
    .reduce((total, cut) => total + Math.max(0, Math.min(cut.end, duration) - Math.max(cut.start, 0)), 0);
  return duration - removed;
}

/** Con «Escuchar sin cortes», un tiempo dentro de un corte activo salta a su final. Fuera de un corte, null. */
export function skipTarget(time: number, cuts: Cut[]): number | null {
  const cut = cuts.find((item) => item.enabled && time >= item.start && time < item.end);
  return cut ? cut.end : null;
}

/** La selección avanza o retrocede una posición y se queda dentro de la lista. */
export function moveSelection(index: number, count: number, step: 1 | -1): number {
  if (count === 0) return 0;
  return Math.min(count - 1, Math.max(0, index + step));
}

/** Activa o desactiva un corte. Queda como editado a mano. */
export function toggleCut(cuts: Cut[], index: number): Cut[] {
  return cuts.map((cut, position) => (position === index ? { ...cut, enabled: !cut.enabled, edited: true } : cut));
}

/** Mueve los bordes de un corte. Queda como editado a mano. */
export function editCut(cuts: Cut[], index: number, start: number, end: number): Cut[] {
  return cuts.map((cut, position) => (position === index ? { ...cut, start, end, edited: true } : cut));
}

/** Minutos, segundos y décimas: 83.4 → 01:23.4. */
export function clock(seconds: number): string {
  const tenths = Math.round(seconds * 10);
  const minutes = Math.floor(tenths / 600);
  const secs = ((tenths % 600) / 10).toFixed(1).padStart(4, '0');
  return `${String(minutes).padStart(2, '0')}:${secs}`;
}

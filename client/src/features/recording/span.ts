// El tramo que se importa: de 8 a 12 segundos (spec 010, D-4 y AC-6). Es el mismo límite que valida el server.
export const MIN_SPAN = 8;
export const MAX_SPAN = 12;

/**
 * Ajusta un tramo a 8–12 s dentro del archivo: conserva el inicio si cabe, y si no lo pega al final del archivo. Un archivo
 * más corto que 8 s devuelve el archivo entero; el server lo rechaza al importar.
 */
export function clampSpan(start: number, end: number, duration: number): { start: number; end: number } {
  const length = Math.min(duration, Math.max(MIN_SPAN, Math.min(MAX_SPAN, end - start)));
  const from = Math.min(Math.max(0, start), Math.max(0, duration - length));
  return { start: from, end: from + length };
}

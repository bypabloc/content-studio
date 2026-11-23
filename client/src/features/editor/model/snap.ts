/**
 * Imán y rejilla del editor (D-8). Funciones puras: la pantalla pasa los candidatos (bordes, cabezal, marcadores,
 * el 0 y la rejilla) y los px por segundo del zoom.
 */

/** Distancia en píxeles de pantalla dentro de la cual un borde se pega. */
export const SNAP_PX = 8;

const GRID_STEPS = [0.1, 0.25, 0.5, 1, 2, 5, 10, 30, 60];
const GRID_MIN_PX = 50;

/** El tiempo `t` pegado al candidato más cercano dentro de `SNAP_PX`; si ninguno está tan cerca, `t` tal cual. */
export function snapTime(t: number, candidates: number[], pxPerSecond: number): number {
  let best = t;
  let bestPx = SNAP_PX;
  for (const candidate of candidates) {
    const px = Math.abs(candidate - t) * pxPerSecond;
    if (px <= bestPx) {
      best = candidate;
      bestPx = px;
    }
  }
  return best;
}

/** El paso de la rejilla: el más pequeño que deja al menos `GRID_MIN_PX` de pantalla entre líneas. */
export function gridStep(pxPerSecond: number): number {
  return GRID_STEPS.find((step) => step * pxPerSecond >= GRID_MIN_PX) ?? GRID_STEPS[GRID_STEPS.length - 1];
}

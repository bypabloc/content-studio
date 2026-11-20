/** Niveles en dBFS de un bloque de muestras (spec 010, D-2): pico y RMS, con un suelo para el silencio. */

export const FLOOR_DBFS = -120;

function toDbfs(linear: number): number {
  return linear > 0 ? Math.max(FLOOR_DBFS, 20 * Math.log10(linear)) : FLOOR_DBFS;
}

/** Pico en dBFS: 0 es el fondo de escala. */
export function peakDbfs(samples: Float32Array): number {
  let peak = 0;
  for (const x of samples) peak = Math.max(peak, Math.abs(x));
  return toDbfs(peak);
}

/** RMS en dBFS: la potencia media, que sigue mejor la sensación de volumen que el pico. */
export function rmsDbfs(samples: Float32Array): number {
  let sum = 0;
  for (const x of samples) sum += x * x;
  return toDbfs(Math.sqrt(sum / Math.max(samples.length, 1)));
}

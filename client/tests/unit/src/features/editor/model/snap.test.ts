// Imán y rejilla del editor (spec 017, D-8): el borde se pega dentro de 8 px de pantalla; la rejilla sigue al zoom.
import { describe, expect, it } from 'vitest';

import { gridStep, snapTime, SNAP_PX } from '@/features/editor/model/snap';

describe('imán del editor (D-8)', () => {
  it('se pega al candidato más cercano dentro de 8 px de pantalla', () => {
    // A 10 px por segundo, 0,7 s son 7 px: se pega. 0,9 s son 9 px: no se pega.
    expect(SNAP_PX).toBe(8);
    expect(snapTime(10.7, [10], 10)).toBe(10);
    expect(snapTime(10.9, [10], 10)).toBe(10.9);
  });

  it('gana el candidato más cercano entre varios', () => {
    expect(snapTime(5.2, [4, 5.4, 9], 10)).toBe(5.4);
  });

  it('la rejilla es el paso más pequeño que deja al menos 50 px entre líneas', () => {
    expect(gridStep(100)).toBe(0.5);
    expect(gridStep(10)).toBe(5);
  });

  it('con el zoom muy alejado, ningún paso llega a 50 px y la rejilla usa el más grande', () => {
    expect(gridStep(0.1)).toBe(60);
  });
});

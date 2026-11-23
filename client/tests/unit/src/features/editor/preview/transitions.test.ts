import { describe, expect, it } from 'vitest';

import { transitionMode, transitionProgress, transitionWeights } from '@/features/editor/preview/transitions';

describe('transiciones de vista previa', () => {
  it('mapea de forma estable cada tipo', () => {
    expect(['fade', 'fadeblack', 'fadewhite', 'wipeleft', 'wiperight', 'slideleft', 'slideright', 'circleopen']
      .map((type) => transitionMode(type as Parameters<typeof transitionMode>[0])))
      .toEqual([1, 2, 3, 4, 5, 6, 7, 8]);
  });

  it('limita el avance al tramo de transicion', () => {
    expect(transitionProgress(2.5, 2, 1)).toBe(0.5);
    expect(transitionProgress(1, 2, 1)).toBe(0);
    expect(transitionProgress(4, 2, 1)).toBe(1);
    expect(transitionProgress(2, 2, 0)).toBe(1);
    expect(transitionProgress(2, 2, -1)).toBe(1);
  });

  it('mezcla fade y fundido a negro y blanco', () => {
    expect(transitionWeights('fade', 0.25, 0.5, 0.5)).toEqual({ from: 0.75, to: 0.25, fill: 0 });
    expect(transitionWeights('fadeblack', 0, 0.5, 0.5)).toEqual({ from: 1, to: 0, fill: 0 });
    expect(transitionWeights('fadeblack', 0.5, 0.5, 0.5)).toEqual({ from: 0, to: 0, fill: 1 });
    expect(transitionWeights('fadewhite', 1, 0.5, 0.5)).toEqual({ from: 0, to: 1, fill: 0 });
    expect(transitionWeights('fade', -1, 0.5, 0.5)).toEqual({ from: 1, to: 0, fill: 0 });
    expect(transitionWeights('fade', 2, 0.5, 0.5)).toEqual({ from: 0, to: 1, fill: 0 });
  });

  it('revela clips con wipe y circleopen segun las coordenadas', () => {
    expect(transitionWeights('wipeleft', 0.4, 0.2, 0.5).to).toBe(1);
    expect(transitionWeights('wipeleft', 0.4, 0.8, 0.5).from).toBe(1);
    expect(transitionWeights('wiperight', 0.4, 0.8, 0.5).to).toBe(1);
    expect(transitionWeights('wiperight', 0.4, 0.2, 0.5).from).toBe(1);
    expect(transitionWeights('circleopen', 0.5, 0.5, 0.5).to).toBe(1);
    expect(transitionWeights('circleopen', 0.1, 0, 0).from).toBe(1);
  });

  it('deja la geometria a cargo de los deslizamientos', () => {
    expect(transitionWeights('slideleft', 0.5, 0.5, 0.5)).toEqual({ from: 1, to: 1, fill: 0 });
    expect(transitionWeights('slideright', 0.5, 0.5, 0.5)).toEqual({ from: 1, to: 1, fill: 0 });
  });
});

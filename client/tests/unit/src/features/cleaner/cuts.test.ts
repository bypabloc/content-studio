import { describe, expect, it } from 'vitest';

import { clock, type Cut, editCut, keepDuration, moveSelection, skipTarget, toggleCut } from '@/features/cleaner/cuts';

const cuts: Cut[] = [
  { start: 1, end: 2, enabled: true },
  { start: 5, end: 6, enabled: false },
  { start: 8, end: 9, enabled: true },
];

describe('cortes (spec 013, D-6)', () => {
  it('la duración resultante resta solo los cortes activos', () => {
    expect(keepDuration(10, cuts)).toBeCloseTo(8);
  });

  it('un corte que pasa del final cuenta solo hasta la duración', () => {
    expect(keepDuration(8.5, [{ start: 8, end: 9, enabled: true }])).toBeCloseTo(8);
  });

  it('la vista previa salta el tramo activo que contiene el tiempo, hasta su final', () => {
    expect(skipTarget(1.5, cuts)).toBe(2);
    expect(skipTarget(8.1, cuts)).toBe(9);
  });

  it('el final del corte no cuenta, y un corte desactivado no salta', () => {
    expect(skipTarget(2, cuts)).toBeNull();
    expect(skipTarget(5.5, cuts)).toBeNull();
    expect(skipTarget(0.5, cuts)).toBeNull();
  });

  it('las flechas mueven la selección sin salir de la lista', () => {
    expect(moveSelection(0, 3, -1)).toBe(0);
    expect(moveSelection(2, 3, 1)).toBe(2);
    expect(moveSelection(0, 3, 1)).toBe(1);
    expect(moveSelection(0, 0, 1)).toBe(0);
  });

  it('desactivar un corte lo marca como editado y no cambia el original', () => {
    const next = toggleCut(cuts, 1);

    expect(next[1]).toEqual({ start: 5, end: 6, enabled: true, edited: true });
    expect(cuts[1].enabled).toBe(false);
  });

  it('mover los bordes de un corte lo marca como editado', () => {
    expect(editCut(cuts, 0, 1.2, 2.1)[0]).toEqual({ start: 1.2, end: 2.1, enabled: true, edited: true });
  });

  it('clock muestra minutos, segundos y décimas', () => {
    expect(clock(83.4)).toBe('01:23.4');
    expect(clock(0)).toBe('00:00.0');
  });
});

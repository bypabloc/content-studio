// Historial del editor (spec 017, D-7): instantáneas inmutables, deshacer y rehacer, tope de 200 pasos.
import { describe, expect, it } from 'vitest';

import { canRedo, canUndo, createHistory, preview, record, redo, undo, MAX_STEPS } from '@/features/editor/model/history';
import type { Doc } from '@/features/editor/model/types';

const doc = (name: string): Doc => ({ version: 1, name, sample_rate: 48000, tracks: [], clips: [], markers: [] });

describe('historial del editor (D-7)', () => {
  it('deshace y rehace a la instantánea anterior y siguiente', () => {
    let h = createHistory(doc('a'));
    h = record(h, doc('b'));
    h = record(h, doc('c'));

    h = undo(h);
    expect(h.present.name).toBe('b');
    h = redo(h);
    expect(h.present.name).toBe('c');
  });

  it('registrar un paso nuevo borra lo que se podía rehacer', () => {
    let h = record(createHistory(doc('a')), doc('b'));
    h = undo(h);
    h = record(h, doc('c'));

    expect(canRedo(h)).toBe(false);
    expect(h.present.name).toBe('c');
  });

  it('no deja deshacer ni rehacer más allá de las instantáneas que hay', () => {
    const h = createHistory(doc('a'));

    expect(canUndo(h)).toBe(false);
    expect(undo(h)).toBe(h);
    expect(canRedo(h)).toBe(false);
    expect(redo(h)).toBe(h);
  });

  it('guarda como máximo MAX_STEPS pasos y olvida los más viejos', () => {
    let h = createHistory(doc('0'));
    for (let i = 1; i <= MAX_STEPS + 10; i += 1) h = record(h, doc(String(i)));

    let steps = 0;
    while (canUndo(h)) {
      h = undo(h);
      steps += 1;
    }
    expect(MAX_STEPS).toBe(200);
    expect(steps).toBe(MAX_STEPS);
  });

  it('una vista previa cambia el documento sin apilar un paso (el arrastre se guarda al soltar)', () => {
    const start = createHistory(doc('a'));
    let h = preview(start, doc('a-arrastrando-1'));
    h = preview(h, doc('a-arrastrando-2'));
    h = record(start, doc('a-final'));

    expect(h.present.name).toBe('a-final');
    expect(undo(h).present.name).toBe('a');
  });
});

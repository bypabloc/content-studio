/**
 * Historial del editor (D-7): una pila de documentos inmutables, con deshacer y rehacer por instantáneas.
 *
 * Un arrastre cambia el documento con `preview` (no apila pasos) y, al soltar, se registra una sola vez con `record`
 * sobre el historial que había antes de empezar: así un arrastre es un solo paso para deshacer.
 */

import type { Doc } from './types';

export const MAX_STEPS = 200;

export interface History {
  past: Doc[];
  present: Doc;
  future: Doc[];
}

export function createHistory(doc: Doc): History {
  return { past: [], present: doc, future: [] };
}

/** Registra un paso nuevo: el documento actual pasa al pasado y se borra lo que se podía rehacer. */
export function record(h: History, next: Doc): History {
  return { past: [...h.past, h.present].slice(-MAX_STEPS), present: next, future: [] };
}

/** Cambia el documento sin apilar un paso: para la vista previa de un arrastre. */
export function preview(h: History, next: Doc): History {
  return { ...h, present: next };
}

export function canUndo(h: History): boolean {
  return h.past.length > 0;
}

export function canRedo(h: History): boolean {
  return h.future.length > 0;
}

export function undo(h: History): History {
  if (!canUndo(h)) return h;
  return { past: h.past.slice(0, -1), present: h.past[h.past.length - 1], future: [h.present, ...h.future] };
}

export function redo(h: History): History {
  if (!canRedo(h)) return h;
  return { past: [...h.past, h.present], present: h.future[0], future: h.future.slice(1) };
}

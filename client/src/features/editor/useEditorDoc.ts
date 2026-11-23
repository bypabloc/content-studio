import { useCallback, useEffect, useRef, useState } from 'react';

import { useApi } from '@/shared/api/context';

import { apply } from './model/ops';
import {
  canRedo as historyCanRedo,
  canUndo as historyCanUndo,
  createHistory,
  preview as previewHistory,
  record,
  redo as redoHistory,
  undo as undoHistory,
  type History,
} from './model/history';
import type { Doc, Op } from './model/types';

type SaveState = 'saved' | 'dirty' | 'saving' | 'error';

type Params = { path: string; doc: Doc; hash: string };

type EditorDoc = {
  doc: Doc;
  hash: string;
  canUndo: boolean;
  canRedo: boolean;
  saveState: SaveState;
  saveError: string | null;
  applyOp: (op: Op) => void;
  undo: () => void;
  redo: () => void;
  previewDoc: (doc: Doc) => void;
  commitPreview: () => void;
  cancelPreview: () => void;
};

export function useEditorDoc({ path, doc: initialDoc, hash: initialHash }: Params): EditorDoc {
  const api = useApi();
  const [history, setHistory] = useState(() => createHistory(initialDoc));
  const historyRef = useRef<History>(history);
  const previewBaseRef = useRef<History | null>(null);
  const docRef = useRef(history.present);
  const hashRef = useRef(initialHash);
  const [hash, setHash] = useState(initialHash);
  const revisionRef = useRef(0);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const flushRef = useRef<() => Promise<void>>(async () => undefined);
  const savingRef = useRef(false);
  const mountedRef = useRef(true);
  const [saveState, setSaveState] = useState<SaveState>('saved');
  const [saveError, setSaveError] = useState<string | null>(null);

  const scheduleSave = useCallback(() => {
    if (timerRef.current !== null) clearTimeout(timerRef.current);
    timerRef.current = setTimeout(() => {
      timerRef.current = null;
      void flushRef.current();
    }, 1000);
  }, []);

  const flush = useCallback(async () => {
    if (savingRef.current) return;
    savingRef.current = true;
    const revision = revisionRef.current;
    const snapshot = docRef.current;
    if (mountedRef.current) setSaveState('saving');
    try {
      const result = await api.put<{ hash: string }>(
        `/editor/projects?path=${encodeURIComponent(path)}`,
        snapshot,
        { 'If-Match': hashRef.current },
      );
      hashRef.current = result.hash;
      if (mountedRef.current) {
        setHash(result.hash);
        setSaveError(null);
        setSaveState(revisionRef.current === revision ? 'saved' : 'dirty');
      }
    } catch (error) {
      if (mountedRef.current) {
        setSaveError(error instanceof Error ? error.message : String(error));
        setSaveState('error');
      }
    } finally {
      savingRef.current = false;
      if (revisionRef.current !== revision) scheduleSave();
    }
  }, [api, path, scheduleSave]);
  useEffect(() => {
    flushRef.current = flush;
  }, [flush]);

  const update = useCallback(
    (next: History) => {
      historyRef.current = next;
      docRef.current = next.present;
      setHistory(next);
      revisionRef.current += 1;
      setSaveState('dirty');
      setSaveError(null);
      scheduleSave();
    },
    [scheduleSave],
  );

  const applyOp = useCallback(
    (op: Op) => {
      previewBaseRef.current = null;
      const current = historyRef.current;
      update(record(current, apply(current.present, op)));
    },
    [update],
  );

  const undo = useCallback(() => {
    const current = previewBaseRef.current ?? historyRef.current;
    previewBaseRef.current = null;
    const next = undoHistory(current);
    if (next !== current) update(next);
  }, [update]);

  const redo = useCallback(() => {
    previewBaseRef.current = null;
    const current = historyRef.current;
    const next = redoHistory(current);
    if (next !== current) update(next);
  }, [update]);

  const previewDoc = useCallback((nextDoc: Doc) => {
    if (previewBaseRef.current === null) previewBaseRef.current = historyRef.current;
    const next = previewHistory(historyRef.current, nextDoc);
    historyRef.current = next;
    docRef.current = next.present;
    setHistory(next);
  }, []);

  const commitPreview = useCallback(() => {
    const base = previewBaseRef.current;
    if (base === null) return;
    previewBaseRef.current = null;
    update(record(base, historyRef.current.present));
  }, [update]);

  const cancelPreview = useCallback(() => {
    const base = previewBaseRef.current;
    if (base === null) return;
    previewBaseRef.current = null;
    historyRef.current = base;
    docRef.current = base.present;
    setHistory(base);
  }, []);

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
      if (timerRef.current !== null) clearTimeout(timerRef.current);
    };
  }, []);

  return {
    doc: history.present,
    hash,
    canUndo: historyCanUndo(history),
    canRedo: historyCanRedo(history),
    saveState,
    saveError,
    applyOp,
    undo,
    redo,
    previewDoc,
    commitPreview,
    cancelPreview,
  };
}

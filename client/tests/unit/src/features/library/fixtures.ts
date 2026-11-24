import type { LibraryItem } from '@/features/library/types';

/** Un ítem de la biblioteca con valores por defecto; las pruebas cambian lo que miden. */
export function libraryItem(change: Partial<LibraryItem> = {}): LibraryItem {
  return {
    id: 1,
    path: 'D:/out/narration/a/take.wav',
    name: 'take.wav',
    kind: 'narration',
    origin: 'job',
    job_id: 10,
    folder_id: null,
    size: 2048,
    mtime: 1_700_000_000,
    duration: 75,
    width: null,
    height: null,
    media_type: 'audio',
    missing: false,
    starred: false,
    tags: [],
    ...change,
  };
}

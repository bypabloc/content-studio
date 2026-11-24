/** Un archivo del índice de la biblioteca (`GET /library`). */
export interface LibraryItem {
  id: number;
  path: string;
  name: string;
  kind: string;
  origin: 'job' | 'watched';
  job_id: number | null;
  folder_id: number | null;
  size: number;
  mtime: number;
  duration: number | null;
  width: number | null;
  height: number | null;
  media_type: 'audio' | 'video' | 'subtitle' | 'other';
  missing: boolean;
  starred: boolean;
  tags: string[];
}

export interface LibraryResult {
  items: LibraryItem[];
  total: number;
}

export interface Folder {
  id: number;
  path: string;
  name: string | null;
}

export interface Project {
  id: number;
  name: string;
  count: number;
}

export interface TagCount {
  name: string;
  count: number;
}

/** El detalle de un ítem con su origen (`GET /library/{id}`). */
export interface ItemDetailData {
  item: LibraryItem;
  job: { id: number; kind: string; params: Record<string, unknown>; created_at: string; elapsed: number | null } | null;
  outputs: LibraryItem[];
  takes: (LibraryItem & { starred: boolean })[];
}

export interface StorageData {
  by_kind: { kind: string; size: number; count: number }[];
  heaviest: LibraryItem[];
  unchosen: LibraryItem[];
  outputs: { path: string; size: number };
  folders: (Folder & { size: number })[];
}

/** Lo que muestra la Biblioteca: todo, lo generado, una carpeta, un proyecto o el espacio. */
export type Scope =
  | { type: 'all' }
  | { type: 'generated' }
  | { type: 'folder'; id: number }
  | { type: 'project'; id: number }
  | { type: 'storage' };

export interface Filters {
  q: string;
  content: boolean;
  kind: string;
  mediaType: string;
  starred: boolean;
  tag: string;
  since: string;
  length: string;
  sort: string;
}

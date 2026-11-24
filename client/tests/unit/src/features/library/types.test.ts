import { describe, expect, it } from 'vitest';

import type { Filters, Scope, StorageData } from '@/features/library/types';

describe('tipos de la Biblioteca (spec 020)', () => {
  it('un alcance es todo, lo generado, una carpeta, un proyecto o el espacio', () => {
    const scopes: Scope[] = [{ type: 'all' }, { type: 'generated' }, { type: 'folder', id: 1 }, { type: 'project', id: 2 }, { type: 'storage' }];
    const filters: Filters = { q: '', content: false, kind: '', mediaType: '', starred: false, tag: '', since: '', length: '', sort: 'date' };
    const storage: StorageData = { by_kind: [], heaviest: [], unchosen: [], outputs: { path: 'out', size: 0 }, folders: [] };

    expect(scopes.map((scope) => scope.type)).toEqual(['all', 'generated', 'folder', 'project', 'storage']);
    expect(filters.sort).toBe('date');
    expect(storage.outputs.size).toBe(0);
  });
});

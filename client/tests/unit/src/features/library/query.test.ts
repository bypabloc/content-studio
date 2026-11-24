import { describe, expect, it } from 'vitest';

import { EMPTY_FILTERS, formatDate, formatDuration, formatSize, kindLabel, libraryQuery, repeatSection, sendLabel } from '@/features/library/query';

const NOW = new Date(2026, 2, 10, 15);

describe('consulta de la Biblioteca (spec 020, D-2)', () => {
  it('sin filtros pide la primera página por fecha', () => {
    expect(libraryQuery(EMPTY_FILTERS, { type: 'all' }, 1, NOW)).toBe('sort=date&page=1&page_size=200');
  });

  it('cada filtro y el alcance van a la consulta; el contenido solo con texto', () => {
    const query = new URLSearchParams(
      libraryQuery(
        { q: ' acta ', content: true, kind: 'music', mediaType: 'audio', starred: true, tag: 'reel', since: 'week', length: 'medium', sort: 'size' },
        { type: 'project', id: 3 },
        2,
        NOW,
      ),
    );

    expect(Object.fromEntries(query)).toEqual({
      sort: 'size', page: '2', page_size: '200', q: 'acta', content: 'true', kind: 'music', media_type: 'audio',
      starred: 'true', tag: 'reel', from: '2026-03-03', min_dur: '60', max_dur: '300', project: '3',
    });
    expect(libraryQuery({ ...EMPTY_FILTERS, content: true }, { type: 'generated' }, 1, NOW)).not.toContain('content');
    expect(libraryQuery(EMPTY_FILTERS, { type: 'generated' }, 1, NOW)).toContain('origin=job');
    expect(libraryQuery({ ...EMPTY_FILTERS, length: 'short', since: 'today' }, { type: 'folder', id: 4 }, 1, NOW)).toBe(
      'sort=date&page=1&page_size=200&from=2026-03-10&max_dur=60&folder=4',
    );
    expect(libraryQuery({ ...EMPTY_FILTERS, length: 'long' }, { type: 'all' }, 1, NOW)).toContain('min_dur=300');
  });

  it('formatea duraciones, tamaños y fechas', () => {
    expect([formatDuration(null), formatDuration(75), formatDuration(3725)]).toEqual(['—', '1:15', '1:02:05']);
    expect([formatSize(512), formatSize(1536), formatSize(200 * 1024 * 1024)]).toEqual(['512 B', '1,5 KB', '200 MB']);
    expect(formatDate(0)).toMatch(/1969|1970/);
  });

  it('cada tipo con sección tiene «Editar y repetir»; los textos dinámicos salen del catálogo', () => {
    expect(['narration', 'music', 'clean', 'subtitles', 'convert', 'mix', 'trim'].map(repeatSection)).toEqual([
      'narration', 'music', 'cleaner', 'subtitles', 'convert', 'mix', null,
    ]);
    expect(kindLabel('music')).toBe('Música');
    expect(sendLabel('cleaner')).toBe('Mandar a Limpiador');
  });
});

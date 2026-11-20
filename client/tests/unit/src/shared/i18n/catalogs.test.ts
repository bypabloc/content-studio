import { describe, expect, it } from 'vitest';
import { CATALOGS } from '@/shared/i18n/catalogs';

describe('CATALOGS', () => {
  it('los tres idiomas tienen las mismas claves que el español', () => {
    const keys = (catalog: Record<string, string>) => Object.keys(catalog).sort();

    expect(keys(CATALOGS.en)).toEqual(keys(CATALOGS.es));
    expect(keys(CATALOGS.pt)).toEqual(keys(CATALOGS.es));
  });
});

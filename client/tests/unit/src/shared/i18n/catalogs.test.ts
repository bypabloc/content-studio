import { describe, expect, it } from 'vitest';
import { CATALOGS, loadCatalog, type Locale } from '@/shared/i18n/catalogs';

describe('CATALOGS', () => {
  it('no incorpora inglés ni portugués al bundle hasta solicitar el idioma', async () => {
    expect(CATALOGS.en).toBeUndefined();
    expect(CATALOGS.pt).toBeUndefined();

    await loadCatalog('en');
    expect(CATALOGS.en?.['nav.settings']).toBe('Settings');
  });

  it('comparte la promesa mientras carga el mismo idioma', async () => {
    const first = loadCatalog('pt');
    const concurrent = loadCatalog('pt');

    expect(concurrent).toBe(first);
    await first;
  });

  it('resuelve sin cargar si no existe un cargador para el idioma', async () => {
    await expect(loadCatalog('fr' as Locale)).resolves.toBeUndefined();
  });

  it('los tres idiomas tienen las mismas claves que el español', async () => {
    await Promise.all([loadCatalog('en'), loadCatalog('pt')]);
    const keys = (catalog: Record<string, string>) => Object.keys(catalog).sort();

    expect(keys(CATALOGS.en!)).toEqual(keys(CATALOGS.es!));
    expect(keys(CATALOGS.pt!)).toEqual(keys(CATALOGS.es!));
  });
});

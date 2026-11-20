import { beforeEach, describe, expect, it } from 'vitest';
import { label, t, type MessageKey } from '@/shared/i18n/t';
import { setLocale } from '@/shared/i18n/locale';

describe('t', () => {
  beforeEach(() => setLocale('es'));

  it('label() da el nombre de un estilo, motor o modelo en el idioma activo', () => {
    expect(label('narration.style', 'expert')).toBe('Experto');
    setLocale('en');
    expect(label('narration.style', 'expert')).toBe('Expert');
  });

  it('usa el idioma activo', () => {
    setLocale('en');
    expect(t('nav.settings')).toBe('Settings');

    setLocale('pt');
    expect(t('nav.settings')).toBe('Configurações');
  });

  it('reemplaza los parámetros también en el idioma activo', () => {
    setLocale('en');

    expect(t('app.version', { version: '1.2.3' })).toBe('Version 1.2.3');
  });

  it('devuelve el texto del catálogo', () => {
    expect(t('app.name')).toBe('Content Studio');
  });

  it('reemplaza los parámetros {nombre}', () => {
    expect(t('app.version', { version: '1.2.3' })).toBe('Versión 1.2.3');
  });

  it('deja el marcador {nombre} si falta el parámetro', () => {
    expect(t('app.version')).toBe('Versión {version}');
  });

  it('devuelve la clave si no existe, para que se note en pantalla', () => {
    expect(t('no.existe' as MessageKey)).toBe('no.existe');
  });
});

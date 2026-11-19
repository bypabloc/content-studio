import { describe, expect, it } from 'vitest';
import { t, type MessageKey } from '@/shared/i18n/t';

describe('t', () => {
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

import { beforeEach, describe, expect, it, vi } from 'vitest';
import { getLocale, readCachedLanguage, resolveLocale, setLocale, subscribe } from '@/shared/i18n/locale';

describe('resolveLocale', () => {
  it('con «system» sigue el primer idioma soportado de la lista del sistema', () => {
    expect(resolveLocale('system', ['pt-BR', 'en'])).toBe('pt');
    expect(resolveLocale('system', ['en-US'])).toBe('en');
  });

  it('con «system» y ningún idioma soportado, usa español', () => {
    expect(resolveLocale('system', ['fr-FR'])).toBe('es');
  });

  it('con un idioma elegido, usa ese aunque el sistema diga otro', () => {
    expect(resolveLocale('en', ['pt-BR'])).toBe('en');
  });
});

describe('setLocale', () => {
  beforeEach(() => {
    localStorage.clear();
    setLocale('es');
  });

  it('cambia el idioma activo y <html lang>', () => {
    setLocale('en');

    expect(getLocale()).toBe('en');
    expect(document.documentElement.lang).toBe('en');
  });

  it('guarda la elección en la caché ui.language', () => {
    setLocale('pt');

    expect(localStorage.getItem('ui.language')).toBe('pt');
  });

  it('avisa a los suscriptores del cambio', () => {
    const listener = vi.fn();
    const unsubscribe = subscribe(listener);

    setLocale('en');
    unsubscribe();
    setLocale('pt');

    expect(listener).toHaveBeenCalledTimes(1);
  });
});

describe('readCachedLanguage', () => {
  beforeEach(() => localStorage.clear());

  it('devuelve la elección guardada', () => {
    localStorage.setItem('ui.language', 'pt');

    expect(readCachedLanguage()).toBe('pt');
  });

  it('sin elección o con un valor que no es un idioma, devuelve «system»', () => {
    expect(readCachedLanguage()).toBe('system');

    localStorage.setItem('ui.language', 'fr');
    expect(readCachedLanguage()).toBe('system');
  });
});

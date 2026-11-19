import { beforeEach, describe, expect, it } from 'vitest';
import { applyTheme, readCachedTheme, resolveTheme, type ThemeMode } from '@/shared/theme/theme';

// Un MediaQueryList simulado: `set` cambia el valor y avisa a los oyentes, como lo hace el sistema.
function fakeMedia(matches: boolean) {
  const listeners = new Set<() => void>();
  const media = {
    matches,
    addEventListener: (_type: string, listener: () => void) => listeners.add(listener),
    removeEventListener: (_type: string, listener: () => void) => listeners.delete(listener),
    set(next: boolean) {
      media.matches = next;
      listeners.forEach((listener) => listener());
    },
  };
  return media;
}

function root(): HTMLElement {
  return document.createElement('html');
}

describe('tema', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('system sigue al sistema y cambia sin recargar', () => {
    const media = fakeMedia(false);
    const html = root();

    const stop = applyTheme('system', media as unknown as MediaQueryList, html);
    expect(html.classList.contains('dark')).toBe(false);

    media.set(true);
    expect(html.classList.contains('dark')).toBe(true);
    stop();
  });

  it('al dejar de seguir al sistema ya no reacciona a sus cambios', () => {
    const media = fakeMedia(false);
    const html = root();

    applyTheme('system', media as unknown as MediaQueryList, html)();
    media.set(true);

    expect(html.classList.contains('dark')).toBe(false);
  });

  it.each<ThemeMode>(['light', 'dark'])('%s fijo ignora al sistema', (mode) => {
    const media = fakeMedia(mode === 'light');
    const html = root();

    applyTheme(mode, media as unknown as MediaQueryList, html);
    media.set(mode === 'dark');

    expect(html.classList.contains('dark')).toBe(mode === 'dark');
  });

  it('guarda la elección en caché en cada cambio', () => {
    applyTheme('dark', fakeMedia(false) as unknown as MediaQueryList, root());
    expect(readCachedTheme()).toBe('dark');

    applyTheme('light', fakeMedia(false) as unknown as MediaQueryList, root());
    expect(readCachedTheme()).toBe('light');
  });

  it('sin caché, o con un valor que no es un modo, la elección es system', () => {
    expect(readCachedTheme()).toBe('system');

    localStorage.setItem('ui.theme', 'neon');
    expect(readCachedTheme()).toBe('system');
  });

  it('resolveTheme: system depende del sistema; light y dark no', () => {
    expect(resolveTheme('system', true)).toBe('dark');
    expect(resolveTheme('system', false)).toBe('light');
    expect(resolveTheme('light', true)).toBe('light');
    expect(resolveTheme('dark', false)).toBe('dark');
  });
});

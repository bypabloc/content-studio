import { cleanup, configure } from '@testing-library/react';
import { afterEach } from 'vitest';

// Menús, diálogos y tooltips de Base UI abren con transiciones: bajo carga (pre-commit, CI de 2 vCPU) el
// timeout por defecto de 1 s no alcanza (spec 008, portado de klinikae `app-kit/testing/setup`).
configure({ asyncUtilTimeout: 5000 });

afterEach(() => {
  cleanup();
});

// jsdom no trae EventSource: la conexión de eventos se prueba con su propio fake; aquí solo evita el error.
if (typeof EventSource === 'undefined') {
  globalThis.EventSource = class {
    addEventListener() {}
    close() {}
  } as unknown as typeof EventSource;
}

// Las pruebas escriben sus expectativas en español: jsdom reporta en-US, así que el idioma «system» daría inglés.
// La caché `ui.language` fija el español antes de cargar cada módulo; las pruebas de idioma la cambian a su gusto.
if (typeof localStorage !== 'undefined') {
  localStorage.setItem('ui.language', 'es');
}

// jsdom no trae matchMedia; el tema lo usa para seguir `prefers-color-scheme`. Los tests en node no tienen window.
if (typeof window !== 'undefined' && !window.matchMedia) {
  window.matchMedia = (query: string) =>
    ({
      matches: false,
      media: query,
      onchange: null,
      addListener() {},
      removeListener() {},
      addEventListener() {},
      removeEventListener() {},
      dispatchEvent: () => false,
    }) as unknown as MediaQueryList;
}

// jsdom tampoco trae ResizeObserver ni las APIs de puntero y scroll que usan Base UI y los selectores.
if (typeof window !== 'undefined') {
  if (!globalThis.ResizeObserver) {
    globalThis.ResizeObserver = class {
      observe(): void {}
      unobserve(): void {}
      disconnect(): void {}
    } as unknown as typeof ResizeObserver;
  }
  Element.prototype.hasPointerCapture ??= () => false;
  Element.prototype.releasePointerCapture ??= () => {};
  Element.prototype.scrollIntoView ??= () => {};
  window.PointerEvent ??= class extends MouseEvent {} as typeof PointerEvent;
}

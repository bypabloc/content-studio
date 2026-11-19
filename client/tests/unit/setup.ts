// jsdom no trae EventSource: la conexión de eventos se prueba con su propio fake; aquí solo evita el error.
if (typeof EventSource === 'undefined') {
  globalThis.EventSource = class {
    addEventListener() {}
    close() {}
  } as unknown as typeof EventSource;
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

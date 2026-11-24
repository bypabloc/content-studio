import type { Page } from '@playwright/test';

/**
 * Simula el diálogo nativo (spec 024, D-6): `plugin:dialog|open` y `plugin:dialog|save` devuelven `paths` sin abrir el
 * selector de Windows; los demás comandos de Tauri siguen su camino. Con `multiple: false`, `open` devuelve una sola
 * ruta, como el diálogo de Tauri.
 *
 * Tauri deja `__TAURI_INTERNALS__.invoke`, `ipc` y `window.ipc` de solo lectura, y guarda su propio `fetch`. Su IPC
 * termina en `window.chrome.webview.postMessage` de WebView2, que se busca en cada llamada y sí se puede redefinir: el
 * mensaje de un diálogo se responde con `runCallback`, como lo haría el proceso de Rust. En el e2e (API simulada, sin
 * WebView2) responde el `invoke` simulado de `support/app.ts` con `__dialogPick`.
 */
export function pickPaths(page: Page, paths: string[]): Promise<void> {
  return page.evaluate((picked) => {
    type Message = { cmd: string; callback: number; payload?: { options?: { multiple?: boolean } } };
    type Webview = { postMessage: (message: string) => void; __realPostMessage?: (message: string) => void };
    const host = window as unknown as {
      __dialogPick: string[];
      chrome?: { webview?: Webview };
      __TAURI_INTERNALS__: { runCallback: (id: number, data: unknown) => void };
    };
    host.__dialogPick = picked;
    const webview = host.chrome?.webview;
    if (!webview) return;
    const real = webview.__realPostMessage ?? webview.postMessage.bind(webview);
    webview.__realPostMessage = real;
    Object.defineProperty(webview, 'postMessage', {
      configurable: true,
      writable: true,
      value: (raw: string) => {
        const message = JSON.parse(raw) as Message;
        if (message.cmd !== 'plugin:dialog|open' && message.cmd !== 'plugin:dialog|save') return real(raw);
        const single = message.cmd === 'plugin:dialog|save' || message.payload?.options?.multiple === false;
        host.__TAURI_INTERNALS__.runCallback(message.callback, single ? (picked[0] ?? null) : picked);
      },
    });
  }, paths);
}

/**
 * Responde `window.confirm`, `alert` y `prompt` sin mostrar nada: en WebView2 son diálogos nativos que CDP no ve y que
 * dejarían la prueba colgada. Devuelve una función que lee los mensajes que la app mostró.
 */
export async function answerDialogs(page: Page, accept: boolean): Promise<() => Promise<string[]>> {
  await page.evaluate((answer) => {
    const asked: string[] = [];
    (window as unknown as { __asked: string[] }).__asked = asked;
    window.confirm = (message?: string) => (asked.push(String(message ?? '')), answer);
    window.alert = (message?: string) => void asked.push(String(message ?? ''));
    window.prompt = (message?: string) => (asked.push(String(message ?? '')), null);
  }, accept);
  return () => page.evaluate(() => (window as unknown as { __asked: string[] }).__asked);
}

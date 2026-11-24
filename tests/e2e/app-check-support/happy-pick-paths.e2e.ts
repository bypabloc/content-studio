import { expect, test } from '@playwright/test';
import { openApp } from '../support/app';
import { answerDialogs, pickPaths } from '../app-check/support/tauri';

test('spec 024 AC-8: pickPaths responde el diálogo del invoke simulado', async ({ page }) => {
  await openApp(page);
  await pickPaths(page, ['C:/x.wav', 'C:/y.wav']);
  const answers = await page.evaluate(async () => {
    const { invoke } = (window as unknown as {
      __TAURI_INTERNALS__: { invoke: (command: string, args?: unknown) => Promise<unknown> };
    }).__TAURI_INTERNALS__;
    return {
      single: await invoke('plugin:dialog|open', { options: { multiple: false } }),
      many: await invoke('plugin:dialog|open', { options: { multiple: true } }),
      connection: await invoke('get_connection'),
    };
  });
  expect(answers).toEqual({
    single: 'C:/x.wav',
    many: ['C:/x.wav', 'C:/y.wav'],
    connection: { baseUrl: 'http://127.0.0.1:9999', token: 'tok' },
  });
});

test('spec 024 AC-8: con WebView2, pickPaths responde por postMessage y deja pasar los demás comandos', async ({ page }) => {
  await openApp(page);
  // El IPC de WebView2 que usa Tauri en Windows: chrome.webview.postMessage y la respuesta por runCallback.
  await page.evaluate(() => {
    const host = window as unknown as Record<string, unknown> & { chrome?: Record<string, unknown> };
    const sent: string[] = [];
    const answered: [number, unknown][] = [];
    host.chrome = { ...host.chrome, webview: { postMessage: (raw: string) => void sent.push(JSON.parse(raw).cmd) } };
    (host.__TAURI_INTERNALS__ as Record<string, unknown>).runCallback = (id: number, data: unknown) => answered.push([id, data]);
    host.__ipc = { sent, answered };
  });
  await pickPaths(page, ['C:/x.wav', 'C:/y.wav']);
  const result = await page.evaluate(() => {
    const host = window as unknown as {
      chrome: { webview: { postMessage: (raw: string) => void } };
      __ipc: { sent: string[]; answered: [number, unknown][] };
    };
    const send = (cmd: string, callback: number, multiple?: boolean) =>
      host.chrome.webview.postMessage(JSON.stringify({ cmd, callback, error: 0, payload: { options: { multiple } } }));
    send('plugin:dialog|open', 1, false);
    send('plugin:dialog|open', 2, true);
    send('plugin:dialog|save', 3);
    send('plugin:app|version', 4);
    return host.__ipc;
  });
  expect(result.answered).toEqual([[1, 'C:/x.wav'], [2, ['C:/x.wav', 'C:/y.wav']], [3, 'C:/x.wav']]);
  expect(result.sent).toEqual(['plugin:app|version']);
});

test('spec 024: answerDialogs responde confirm sin mostrarlo y guarda el mensaje', async ({ page }) => {
  await openApp(page);
  const asked = await answerDialogs(page, false);
  expect(await page.evaluate(() => window.confirm('¿Mover?'))).toBe(false);
  expect(await asked()).toEqual(['¿Mover?']);
});

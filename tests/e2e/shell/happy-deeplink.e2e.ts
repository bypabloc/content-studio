import { expect, test } from '@playwright/test';
import { hasListener, openApp } from '../support/app';

import type { Page } from '@playwright/test';

/** Dispara `external-request` con el argv de un enlace, como lo haría Rust al recibir un segundo arranque (spec 031, AC-5). */
function emitExternal(page: Page, argv: string[]) {
  return page.evaluate(
    (args) => (window as unknown as { __emitEvent: (event: string, payload: unknown) => void }).__emitEvent('external-request', args),
    argv,
  );
}

// Enlaces con la app abierta (spec 031, AC-1 y AC-3): open/music cambia la sección; new/narration muestra el texto
// y la voz, y no encola nada hasta pulsar Generar.
test('AC-1: un enlace open/music abre Música con la ventana abierta', async ({ page }) => {
  await openApp(page);
  await expect.poll(() => hasListener(page, 'external-request')).toBe(true);
  await emitExternal(page, ['content-studio.exe', 'content-studio://open/music']);
  await expect(page).toHaveURL(/#\/music$/);
});

test('AC-3: un enlace new/narration prellena Narración y no encola nada', async ({ page }) => {
  const { calls } = await openApp(page);
  await expect.poll(() => hasListener(page, 'external-request')).toBe(true);
  await emitExternal(page, ['content-studio.exe', 'content-studio://new/narration?text=Hola%2C%20mundo.&voice=yesid']);
  await expect(page.getByRole('textbox', { name: 'Guion' })).toHaveValue('Hola, mundo.');
  expect(calls.some((call) => call.method === 'POST' && call.path === '/jobs')).toBe(false);
});

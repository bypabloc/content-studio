import { expect, test } from '@playwright/test';
import { openApp } from '../support/app';

test('la cola: progreso en vivo, reordenar con teclado, pausar, cancelar y reintentar (AC-6)', async ({ page }) => {
  const { calls } = await openApp(page);
  await expect(page.locator('[data-job="1"]').getByText('40 %')).toBeVisible();

  // Reordenar: el asa del trabajo 3 sube sobre el 2 (teclado: Espacio, flecha arriba, Espacio). Cada tecla espera su
  // anuncio en la región de estado: dnd-kit calcula sobre qué fila está tras medir las filas, y una flecha antes no mueve.
  const status = page.getByRole('status');
  await page.locator('[data-job="3"] button[aria-label="Mover trabajo"]').focus();
  await page.keyboard.press('Space');
  await expect(status).toHaveText(/posición 2 de 2/);
  // dnd-kit registra su listener de teclas en un setTimeout al tomar el trabajo: un turno del event loop basta.
  await page.evaluate(() => new Promise((done) => setTimeout(done)));
  await page.keyboard.press('ArrowUp');
  await expect(status).toHaveText(/posición 1 de 2/);
  await page.keyboard.press('Space');
  await expect.poll(() => calls.find((call) => call.method === 'PUT' && call.path === '/queue/order')?.body).toEqual({
    ids: [3, 2],
  });

  await page.getByRole('button', { name: 'Pausar' }).click();
  await expect(page.getByRole('button', { name: 'Reanudar' })).toBeVisible();
  await expect.poll(() => calls.some((call) => call.method === 'POST' && call.path === '/queue/pause')).toBe(true);

  await page.locator('[data-job="2"]').getByRole('button', { name: 'Cancelar' }).click();
  await expect.poll(() => calls.some((call) => call.method === 'POST' && call.path === '/jobs/2/cancel')).toBe(true);

  await page.locator('[data-job="4"]').getByRole('button', { name: 'Reintentar' }).click();
  await expect.poll(() => calls.some((call) => call.method === 'POST' && call.path === '/jobs/4/retry')).toBe(true);
});

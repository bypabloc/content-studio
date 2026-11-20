import { expect, test } from '@playwright/test';
import { openApp } from '../support/app';
import { newVoicesState, openAna, voicesReplies } from '../support/voices';

test('AC-8: grabar un estilo y parar sube la toma como WAV, y la toma aparece con su veredicto', async ({ page }) => {
  const state = newVoicesState();
  const { calls } = await openApp(page, { replies: voicesReplies(state) });
  await openAna(page);
  await page.getByRole('button', { name: 'Grabar', exact: true }).click();

  // El micrófono es simulado (launchOptions en playwright.config.ts): el asistente abre, graba y para; la toma sube sola.
  await page.getByRole('button', { name: 'Grabar', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Parar', exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Parar', exact: true }).click();

  await expect
    .poll(() => calls.some((call) => call.method === 'POST' && call.path === '/voices/profiles/ana/takes/neutral'))
    .toBe(true);
  await expect(page.getByText('Bien: lista para elegir')).toBeVisible();
});

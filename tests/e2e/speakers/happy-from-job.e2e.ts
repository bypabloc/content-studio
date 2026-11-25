import { expect, test } from '@playwright/test';
import { openApp } from '../support/app';
import { speakersReplies } from '../support/speakers';

test('abrir una identificación terminada desde la cola muestra su resultado sin encolar otra', async ({ page }) => {
  const { calls } = await openApp(page, { replies: speakersReplies() });
  await page.evaluate(() => {
    window.location.hash = '#/speakers?from_job=7';
  });

  // AC-7: el resultado llega del trabajo guardado; la sección no crea un trabajo nuevo
  await expect(page.getByRole('group', { name: 'Línea de tiempo de hablantes', exact: true })).toBeVisible();
  expect(calls.some((call) => call.method === 'POST' && call.path === '/jobs')).toBe(false);
});

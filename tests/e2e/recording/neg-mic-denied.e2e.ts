import { expect, test } from '@playwright/test';
import { openApp } from '../support/app';
import { newVoicesState, openAna, voicesReplies } from '../support/voices';

test('neg AC-8: si el micrófono no abre, la toma no empieza y el asistente lo dice', async ({ page }) => {
  // El permiso del micrófono se niega: getUserMedia rechaza antes de que la app grabe nada.
  await page.addInitScript(() => {
    navigator.mediaDevices.getUserMedia = () => Promise.reject(new DOMException('Permiso denegado', 'NotAllowedError'));
  });
  const state = newVoicesState();
  const { calls } = await openApp(page, { replies: voicesReplies(state) });
  await openAna(page);
  await page.getByRole('button', { name: 'Grabar', exact: true }).click();
  await page.getByRole('button', { name: 'Grabar', exact: true }).click();

  await expect(page.getByText('No se pudo abrir el micrófono. Revisa el permiso de la app.')).toBeVisible();
  expect(calls.some((call) => call.method === 'POST' && call.path.includes('/takes/'))).toBe(false);
});

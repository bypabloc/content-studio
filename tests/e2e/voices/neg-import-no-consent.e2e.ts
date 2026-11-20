import { expect, test } from '@playwright/test';
import { openApp, setDialogPick } from '../support/app';
import { pickOption } from '../support/select';
import { newVoicesState, openAna, voicesReplies } from '../support/voices';

test('neg AC-6: sin el permiso del dueño, Importar tramo no se puede pulsar y nada sale al server', async ({ page }) => {
  const state = newVoicesState();
  const { calls } = await openApp(page, { replies: voicesReplies(state) });
  await setDialogPick(page, ['C:/media/entrevista.mp4']);
  await openAna(page);

  await page.getByRole('button', { name: 'Importar', exact: true }).click();
  await page.getByRole('button', { name: 'Elegir archivo' }).click();
  await expect(page.getByText('entrevista.mp4')).toBeVisible();
  await pickOption(page, 'Estilo', 'Neutro');
  await page.getByRole('spinbutton', { name: /Inicio/ }).fill('2');
  await page.getByRole('spinbutton', { name: /Fin/ }).fill('10');

  await expect(page.getByRole('button', { name: 'Importar tramo' })).toBeDisabled();
  expect(calls.some((call) => call.method === 'POST' && call.path === '/voices/profiles/ana/import')).toBe(false);
});

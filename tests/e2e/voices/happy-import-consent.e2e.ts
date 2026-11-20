import { expect, test } from '@playwright/test';
import { openApp, setDialogPick } from '../support/app';
import { pickOption } from '../support/select';
import { newVoicesState, openAna, voicesReplies } from '../support/voices';

test('AC-6: importar un tramo con el permiso del dueño lo manda al server y vuelve a la ficha', async ({ page }) => {
  const state = newVoicesState();
  const { calls } = await openApp(page, { replies: voicesReplies(state) });
  await setDialogPick(page, ['C:/media/entrevista.mp4']);
  await openAna(page);

  await page.getByRole('button', { name: 'Importar', exact: true }).click();
  await page.getByRole('button', { name: 'Elegir archivo' }).click();
  await expect(page.getByText('entrevista.mp4')).toBeVisible();
  // La onda del origen llega y propone el tramo de 0 a 10 s (spec 010, D-4).
  await expect(page.getByRole('spinbutton', { name: /Fin/ })).toHaveValue('10');
  await pickOption(page, 'Estilo', 'Neutro');
  await page.getByRole('spinbutton', { name: /Inicio/ }).fill('2');
  await page.getByRole('spinbutton', { name: /Fin/ }).fill('10');
  await page
    .getByRole('checkbox', {
      name: 'Tengo permiso de la persona cuya voz voy a importar y del derecho a usar este audio en mis narraciones.',
    })
    .click();
  await page.getByRole('button', { name: 'Importar tramo' }).click();

  await expect
    .poll(() => calls.find((call) => call.method === 'POST' && call.path === '/voices/profiles/ana/import')?.body)
    .toEqual({ path: 'C:/media/entrevista.mp4', start: 2, end: 10, style: 'neutral', consent: true });
  await expect(page.getByRole('button', { name: 'Grabar', exact: true })).toBeVisible();
});

import { join } from 'node:path';
import { DATA, expect, RUN, test } from './fixture';
import { answerDialogs, pickPaths } from './support/tauri';

// El diálogo nativo simulado llega a la pantalla real (spec 024, AC-8): Almacenamiento pide confirmar el traslado a la
// carpeta elegida, y la prueba responde que no, así no se mueve nada.
test('dialog-pick: the simulated folder reaches Storage without opening the Windows picker', async ({ app, shot }) => {
  const target = join(RUN || 'tmp/app-check', DATA === 'real' ? 'never-used' : 'picked-engines');
  await app.locator('a[href="#/settings"]').first().click();
  await expect(app.getByRole('heading', { name: 'Almacenamiento' })).toBeVisible();
  const asked = await answerDialogs(app, false);
  await pickPaths(app, [target]);
  await app.getByRole('button', { name: 'Cambiar carpeta de motores' }).click();
  await expect.poll(async () => (await asked()).some((message) => message.includes(target))).toBe(true);
  await shot('dialog-pick');
});

import { expect, test } from '@playwright/test';
import { openApp } from '../support/app';
import { goToNarration, narrationReplies, type NarrationState } from '../support/narration';

test('AC-7: elegir un motor no comercial pide la licencia; cancelar deja el motor de antes y no guarda nada', async ({
  page,
}) => {
  const state: NarrationState = { jobs: [] };
  const { calls } = await openApp(page, { replies: narrationReplies(state) });
  await goToNarration(page);
  const engine = page.getByRole('combobox', { name: 'Motor' });
  await expect(engine).toHaveValue(/voxcpm2/);

  // El motor es un combobox (UISelect, spec 008): se abre y se elige la opción por su nombre, no con selectOption.
  await engine.click();
  await page.getByRole('option', { name: /omnivoice/i }).click();

  const dialog = page.getByRole('dialog', { name: 'Licencia de omnivoice' });
  await expect(dialog).toBeVisible();
  await dialog.getByRole('button', { name: 'Cancelar' }).click();

  await expect(dialog).toBeHidden();
  await expect(engine).toHaveValue(/voxcpm2/);
  expect(calls.some((call) => call.method === 'PUT' && call.path.startsWith('/settings/narration.license'))).toBe(false);
});

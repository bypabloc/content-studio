import { expect, test } from '@playwright/test';
import { openApp } from '../support/app';

test('cancelar Cambiar token no cambia el token ni reconecta (AC-11)', async ({ page }) => {
  page.on('dialog', (dialog) => void dialog.dismiss());
  await openApp(page);
  await page.evaluate(() => {
    location.hash = '#/settings';
  });

  // La señal real es el diálogo: al cerrarlo con «Cancelar», confirm() devuelve false y no se pide el cambio.
  const dialog = page.waitForEvent('dialog');
  await page.getByRole('button', { name: 'Cambiar token' }).click();
  await dialog;
  await page.waitForLoadState('networkidle');

  const commands = await page.evaluate(() => (window as unknown as { __commands: string[] }).__commands);
  expect(commands).not.toContain('rotate_token');
  expect(commands.filter((command) => command === 'get_connection')).toHaveLength(1);
});

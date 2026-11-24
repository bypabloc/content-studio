import { expect, test } from '@playwright/test';
import { openApp } from '../support/app';
import { pickOption } from '../support/select';

test('el tema cambia en vivo y Restablecer borra solo las elecciones de los selectores (AC-2, AC-4)', async ({
  page,
}) => {
  page.on('dialog', (dialog) => void dialog.accept());
  const { calls } = await openApp(page);
  await page.evaluate(() => {
    location.hash = '#/settings';
  });

  await pickOption(page, 'Tema', 'Oscuro');
  await expect(page.locator('html')).toHaveClass(/dark/);

  await page.getByRole('button', { name: 'Restablecer elecciones' }).click();
  await expect
    .poll(() => calls.some((call) => call.method === 'DELETE' && call.search === '?prefix=select.'))
    .toBe(true);
  await expect(page.locator('html')).toHaveClass(/dark/);
});

import { expect, test } from '@playwright/test';
import { openApp } from '../support/app';

test('Ctrl+K busca «ajus» y Enter lleva a Ajustes (AC-7)', async ({ page }) => {
  await openApp(page);
  await expect(page.getByRole('heading', { name: 'Content Studio' })).toBeVisible();

  await page.keyboard.press('Control+K');
  await page.getByRole('combobox').fill('ajus');
  await page.keyboard.press('Enter');

  await expect(page).toHaveURL(/#\/settings$/);
  await expect(page.getByRole('main').getByRole('heading', { name: 'Ajustes', level: 2 })).toBeVisible();
});

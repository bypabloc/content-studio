import { expect, test } from '@playwright/test';
import { openApp } from '../support/app';

const collapsed = '[data-collapsible="icon"]';
const toggle = { name: 'Mostrar u ocultar el menú' };

test('el botón y Ctrl+B colapsan la barra a íconos, y sigue colapsada al recargar (AC-7)', async ({ page }) => {
  await openApp(page, { settings: { 'ui.sidebar.collapsed': false } });
  await expect(page.getByRole('heading', { name: 'Content Studio' })).toBeVisible();
  await expect(page.locator(collapsed)).toHaveCount(0);

  await page.getByRole('button', toggle).click();
  await expect(page.locator(collapsed)).toHaveCount(1);
  await page.getByRole('link', { name: 'Narración' }).hover();
  await expect(page.getByRole('tooltip')).toHaveText('Narración');

  await page.keyboard.press('Control+b');
  await expect(page.locator(collapsed)).toHaveCount(0);

  await page.getByRole('button', toggle).click();
  await page.reload();
  await expect(page.locator(collapsed)).toHaveCount(1);
});

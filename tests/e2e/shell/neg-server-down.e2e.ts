import { expect, test } from '@playwright/test';
import { openApp } from '../support/app';

test('si el server no arranca, la ventana dice por qué y ofrece Reintentar (AC-10)', async ({ page }) => {
  await openApp(page, { connect: 'spawn_failed' });

  await expect(page.getByText('No se encontró uv', { exact: false })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Reintentar' })).toBeVisible();
});

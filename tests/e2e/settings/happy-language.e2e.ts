import AxeBuilder from '@axe-core/playwright';
import { expect, test } from '@playwright/test';
import { openApp } from '../support/app';

const serious = (violations: { impact?: string | null }[]) =>
  violations.filter((violation) => violation.impact === 'serious' || violation.impact === 'critical');

test('el idioma cambia la UI en vivo, se guarda y Restablecer no lo cambia (AC-8)', async ({ page }) => {
  page.on('dialog', (dialog) => void dialog.accept());
  const { calls } = await openApp(page);
  await page.evaluate(() => {
    location.hash = '#/settings';
  });

  await page.getByLabel('Idioma', { exact: true }).selectOption('en');
  await expect(page.getByRole('navigation').getByRole('link', { name: 'Narration' })).toBeVisible();
  await expect
    .poll(() =>
      calls.some(
        (call) =>
          call.method === 'PUT' &&
          call.path === '/settings/ui.language' &&
          (call.body as { value: unknown }).value === 'en',
      ),
    )
    .toBe(true);

  await page.getByRole('button', { name: 'Reset choices' }).click();
  await expect
    .poll(() => calls.some((call) => call.method === 'DELETE' && call.search === '?prefix=select.'))
    .toBe(true);
  await expect(page.getByRole('navigation').getByRole('link', { name: 'Narration' })).toBeVisible();
});

test('al reiniciar, la primera pantalla sale en el idioma guardado (AC-8)', async ({ page }) => {
  await openApp(page, { settings: { 'ui.language': 'en' } });

  await expect(page.getByRole('navigation').getByRole('link', { name: 'Narration' })).toBeVisible();
});

test('la opción Sistema lleva la ★ y axe no reporta fallos serios en inglés ni en portugués (AC-8)', async ({
  page,
}) => {
  await openApp(page);
  await page.evaluate(() => {
    location.hash = '#/settings';
  });
  await expect(page.getByRole('option', { name: '★ Sistema', exact: true })).toHaveCount(1);

  // La etiqueta del selector cambia con el idioma: en inglés es «Language».
  await page.getByLabel('Idioma', { exact: true }).selectOption('en');
  await expect(page.getByRole('navigation').getByRole('link', { name: 'Narration' })).toBeVisible();
  expect(serious((await new AxeBuilder({ page }).analyze()).violations)).toEqual([]);

  await page.getByLabel('Language', { exact: true }).selectOption('pt');
  await expect(page.getByRole('navigation').getByRole('link').first()).toBeVisible();
  expect(serious((await new AxeBuilder({ page }).analyze()).violations)).toEqual([]);
});

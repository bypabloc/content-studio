import AxeBuilder from '@axe-core/playwright';
import { expect, test } from '@playwright/test';
import { openApp } from '../support/app';
import { pickOption } from '../support/select';

const serious = (violations: { impact?: string | null }[]) =>
  violations.filter((violation) => violation.impact === 'serious' || violation.impact === 'critical');

test('el idioma cambia la UI en vivo, se guarda y Restablecer no lo cambia (AC-8)', async ({ page }) => {
  page.on('dialog', (dialog) => void dialog.accept());
  const { calls } = await openApp(page);
  await page.evaluate(() => {
    location.hash = '#/settings';
  });

  await pickOption(page, 'Idioma', 'English');
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
  // El ★ va en la opción Sistema del selector de idioma, no en el de tema; las opciones existen con el listado abierto.
  await page.getByRole('combobox', { name: 'Idioma', exact: true }).click();
  await expect(page.getByRole('option', { name: '★ Sistema', exact: true })).toHaveCount(1);
  await page.keyboard.press('Escape');

  // La etiqueta del selector cambia con el idioma: en inglés es «Language».
  await pickOption(page, 'Idioma', 'English');
  await expect(page.getByRole('navigation').getByRole('link', { name: 'Narration' })).toBeVisible();
  await page.addStyleTag({ content: '*, *::before, *::after { animation: none !important; transition: none !important; }' });
  expect(serious((await new AxeBuilder({ page }).analyze()).violations)).toEqual([]);

  await pickOption(page, 'Language', 'Português');
  await expect(page.getByRole('navigation').getByRole('link').first()).toBeVisible();
  await page.addStyleTag({ content: '*, *::before, *::after { animation: none !important; transition: none !important; }' });
  expect(serious((await new AxeBuilder({ page }).analyze()).violations)).toEqual([]);
});

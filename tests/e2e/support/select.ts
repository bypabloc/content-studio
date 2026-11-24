import type { Page } from '@playwright/test';

/**
 * Elige una opción de un selector de la UI (UISelect, spec 008): abre el combobox por su nombre accesible y pulsa la
 * opción por su nombre. No es un `selectOption`: el selector no es un `<select>` nativo.
 */
export async function pickOption(page: Page, combobox: string, option: string): Promise<void> {
  await page.getByRole('combobox', { name: combobox, exact: true }).click();
  await page.getByRole('option', { name: option, exact: true }).click();
}

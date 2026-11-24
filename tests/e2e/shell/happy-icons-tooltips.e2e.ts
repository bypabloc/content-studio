import { expect, test, type Locator, type Page } from '@playwright/test';
import { openApp } from '../support/app';
import { goToNarration, narrationReplies, type NarrationState, take } from '../support/narration';

// Un botón de solo ícono se explica por su texto de ayuda: al recibir el foco, el tooltip dice lo mismo que su nombre
// accesible (spec 009, AC-4). El foco llega con el teclado (Shift+Tab y Tab de vuelta), no con un `focus()` por script.
async function showsTooltip(page: Page, button: Locator, text: string): Promise<void> {
  await button.focus();
  await page.keyboard.press('Shift+Tab');
  await page.keyboard.press('Tab');
  // El tooltip del vecino (el que se cierra) puede seguir en el DOM y decir lo mismo: el portal añade el nuevo al final.
  await expect(page.getByRole('tooltip').filter({ hasText: text }).last()).toBeVisible();
}

test('la barra y la cola: cada botón de solo ícono muestra su tooltip al recibir el foco (AC-4)', async ({ page }) => {
  await openApp(page, { settings: { 'ui.theme': 'light' } });
  await expect(page.locator('[data-job="2"]')).toBeVisible();

  await showsTooltip(page, page.getByRole('button', { name: 'Mostrar u ocultar el menú' }), 'Mostrar u ocultar el menú');
  await showsTooltip(page, page.getByRole('button', { name: 'Claro: cambiar a Oscuro' }), 'Claro: cambiar a Oscuro');
  await showsTooltip(page, page.getByRole('button', { name: 'Pausar' }), 'Pausar');
  await showsTooltip(page, page.getByRole('button', { name: 'Ocultar cola' }), 'Ocultar cola');
  await showsTooltip(page, page.locator('[data-job="2"]').getByRole('button', { name: 'Mover trabajo' }), 'Mover trabajo');
  await showsTooltip(page, page.locator('[data-job="2"]').getByRole('button', { name: 'Cancelar' }), 'Cancelar');
  await showsTooltip(page, page.locator('[data-job="4"]').getByRole('button', { name: 'Reintentar' }), 'Reintentar');
});

test('la narración: Importar, Comparar, Reproducir y Regenerar muestran su tooltip (AC-4)', async ({ page }) => {
  const state: NarrationState = { jobs: [take(3, 'voxcpm2'), take(4, 'omnivoice', 'narration.regenerate')] };
  await openApp(page, { replies: narrationReplies(state) });
  await goToNarration(page);

  await showsTooltip(page, page.getByRole('button', { name: 'Importar' }), 'Importar');
  await showsTooltip(page, page.getByRole('button', { name: 'Comparar' }), 'Comparar');
  await showsTooltip(page, page.getByRole('button', { name: 'Reproducir' }).first(), 'Reproducir');
  await showsTooltip(page, page.getByRole('button', { name: 'Regenerar' }).first(), 'Regenerar');
});

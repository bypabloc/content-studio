import { mkdirSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import AxeBuilder from '@axe-core/playwright';
import { expect, test } from '@playwright/test';
import { openApp } from '../support/app';

// Capturas en claro y oscuro para la revisión visual (tmp/e2e/, command-output.md) y axe sin fallos serios (AC-9).
const OUT = fileURLToPath(new URL('../../../tmp/e2e/', import.meta.url));
mkdirSync(OUT, { recursive: true });

const serious = (violations: { impact?: string | null }[]) =>
  violations.filter((violation) => violation.impact === 'serious' || violation.impact === 'critical');

for (const theme of ['light', 'dark'] as const) {
  test(`shell y ajustes en ${theme}: sin fallos serios de axe, y capturas`, async ({ page }) => {
    await openApp(page, { settings: { 'ui.theme': theme } });
    await expect(page.getByRole('heading', { name: 'Content Studio' })).toBeVisible();
    await page.screenshot({ path: `${OUT}shell-${theme}.png` });
    expect(serious((await new AxeBuilder({ page }).analyze()).violations)).toEqual([]);

    await page.evaluate(() => {
      location.hash = '#/settings';
    });
    await expect(page.getByRole('button', { name: 'Restablecer elecciones' })).toBeVisible();
    await page.screenshot({ path: `${OUT}settings-${theme}.png` });
    expect(serious((await new AxeBuilder({ page }).analyze()).violations)).toEqual([]);
  });
}

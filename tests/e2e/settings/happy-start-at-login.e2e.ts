import { expect, test } from '@playwright/test';
import { openApp } from '../support/app';

// «Iniciar el servidor con Windows» (spec 031, AC-8): el interruptor llama al comando de la app. El valor del registro
// se comprueba aparte, con la app instalada (verificación final).
test('AC-8: el interruptor de inicio con Windows llama al comando de la app', async ({ page }) => {
  await openApp(page);
  await page.evaluate(() => {
    window.location.hash = '#/settings';
  });
  const toggle = page.getByRole('checkbox', { name: 'Iniciar el servidor con Windows' });
  await toggle.scrollIntoViewIfNeeded();
  await toggle.click();
  await expect(toggle).toBeChecked();
  await expect
    .poll(() => page.evaluate(() => (window as unknown as { __commands: string[] }).__commands.includes('set_start_at_login')))
    .toBe(true);
});

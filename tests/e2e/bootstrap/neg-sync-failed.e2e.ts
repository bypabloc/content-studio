import { expect, test } from '@playwright/test';
import { emitEvent, hasListener, openApp } from '../support/app';

test('AC-5 (spec 022): si falla la preparación, la pantalla muestra cada paso, el motivo, y Reintentar abre la app', async ({ page }) => {
  await openApp(page, { connect: 'bootstrap_sync_failed' });

  await expect(page.getByRole('heading', { name: 'Preparando Content Studio' })).toBeVisible();
  await expect.poll(() => hasListener(page, 'bootstrap')).toBe(true);
  const log = 'C:/Users/prueba/AppData/Local/Content Studio/logs/bootstrap.log';
  await emitEvent(page, 'bootstrap', { step: 'python', state: 'done', log });
  await emitEvent(page, 'bootstrap', { step: 'sync', state: 'failed', log });

  await expect(page.getByText('Python 3.12: listo')).toBeVisible();
  await expect(page.getByText('Librerías del motor: falló')).toBeVisible();
  await expect(page.getByText('No se pudieron instalar las librerías del motor. Revisa tu conexión y el log.')).toBeVisible();
  await expect(page.getByRole('button', { name: 'Ver log' })).toBeVisible();

  await page.getByRole('button', { name: 'Reintentar' }).click();
  await expect(page.getByRole('heading', { name: 'Content Studio' })).toBeVisible();
});

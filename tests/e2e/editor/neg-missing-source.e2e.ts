import { expect, test } from '@playwright/test';

import { setDialogPick } from '../support/app';
import { editorState, openEditor } from '../support/editor';

test('AC-10: informa de la fuente ausente y permite reasignarla', async ({ page }) => {
  const state = editorState(true);
  await openEditor(page, state);
  const alert = page.getByRole('alert');
  await expect(alert.getByText('Fuente no encontrada: D:/missing/voz.wav')).toBeVisible();
  await page.getByRole('button', { name: 'Exportar…' }).click();
  const exportDialog = page.getByRole('dialog', { name: 'Exportar proyecto' });
  await exportDialog.getByRole('checkbox', { name: 'Solo audio' }).check();
  await exportDialog.getByRole('button', { name: 'Iniciar exportación' }).click();
  await expect(page.getByText('No se encontraron estas fuentes: D:/missing/voz.wav')).toBeVisible();

  await setDialogPick(page, ['D:/media/voz.wav']);
  await alert.getByRole('button', { name: 'Buscar…' }).click();
  await expect(alert).toHaveCount(0);
  await expect.poll(() => (state.project.doc.clips as Array<{ src: string }>)[0].src).toBe('D:/media/voz.wav');
});

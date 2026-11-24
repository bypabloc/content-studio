// cspell:ignore playhead: identificador del cabezal de reproducción del Editor
import { expect, test } from '@playwright/test';

import { setDialogPick } from '../support/app';
import { editorState, openEditor, requestBodies } from '../support/editor';

test('AC-7/8: importa un audio, lo divide y encola la exportación', async ({ page }) => {
  const state = editorState();
  const calls = await openEditor(page, state);
  const workspace = page.getByRole('region', { name: 'Proyecto demo' });
  const browser = page.getByRole('region', { name: 'Explorador' });
  await expect(browser.getByRole('button', { name: 'musica.wav' })).toBeVisible();
  await setDialogPick(page, ['D:/media/musica.wav']);
  await browser.getByRole('button', { name: 'Importar' }).click();
  await expect(page.getByRole('button', { name: 'musica.wav: 0.0–4.0' })).toBeVisible();

  await page.getByRole('toolbar', { name: 'Transporte de la línea de tiempo' }).getByRole('button', { name: 'Reproducir' }).click();
  const playhead = page.getByRole('img', { name: 'Cabezal de reproducción' });
  await expect.poll(async () => Number.parseFloat((await playhead.getAttribute('style') ?? '').match(/left:\s*([\d.]+)px/)?.[1] ?? '0')).toBeGreaterThan(80);
  await workspace.press('Space');
  await expect(page.getByRole('toolbar', { name: 'Transporte de la línea de tiempo' }).getByRole('button', { name: 'Reproducir' })).toBeVisible();
  await page.getByRole('button', { name: 'voz.wav: 0.0–8.0' }).click();
  await workspace.press('s');
  await expect(page.getByRole('button', { name: /voz\.wav:/ })).toHaveCount(2);
  await expect.poll(() => (state.project.doc.clips as unknown[]).length).toBe(3);

  await page.getByRole('button', { name: 'Exportar…' }).click();
  const exportDialog = page.getByRole('dialog', { name: 'Exportar proyecto' });
  await exportDialog.getByRole('checkbox', { name: 'Solo audio' }).check();
  await exportDialog.getByRole('button', { name: 'Iniciar exportación' }).click();
  await expect.poll(() => requestBodies(calls, '/jobs', 'POST')).toContainEqual(expect.objectContaining({ kind: 'editor.render' }));
});

// cspell:ignore playhead: identificador del cabezal de reproducción del Editor
import { expect, test } from '@playwright/test';

import { editorState, openEditor, requestBodies } from '../support/editor';

test('AC-7/8: exporta tramos consecutivos delimitados por marcadores', async ({ page }) => {
  const state = editorState();
  const calls = await openEditor(page, state);
  const workspace = page.getByRole('region', { name: 'Proyecto demo' });
  const toolbar = page.getByRole('toolbar', { name: 'Transporte de la línea de tiempo' });
  const playhead = page.getByRole('img', { name: 'Cabezal de reproducción' });

  await toolbar.getByRole('button', { name: 'Reproducir' }).click();
  await expect.poll(async () => Number.parseFloat((await playhead.getAttribute('style') ?? '').match(/left:\s*([\d.]+)px/)?.[1] ?? '0')).toBeGreaterThan(80);
  await workspace.press('m');
  await expect(page.getByRole('button', { name: 'Marcador 1' })).toBeVisible();
  await expect.poll(async () => Number.parseFloat((await playhead.getAttribute('style') ?? '').match(/left:\s*([\d.]+)px/)?.[1] ?? '0')).toBeGreaterThan(240);
  await workspace.press('m');
  await expect(page.getByRole('button', { name: 'Marcador 2' })).toBeVisible();
  await workspace.press('Space');

  await page.getByRole('button', { name: 'Exportar…' }).click();
  const exportDialog = page.getByRole('dialog', { name: 'Exportar proyecto' });
  await exportDialog.getByRole('checkbox', { name: 'Solo audio' }).check();
  await exportDialog.getByRole('button', { name: 'Exportar por marcadores' }).click();
  await expect.poll(() => requestBodies(calls, '/jobs', 'POST')).toHaveLength(3);
  const renders = requestBodies(calls, '/jobs', 'POST') as Array<{ params: { start?: number; end?: number } }>;
  expect(renders[0].params.start).toBe(0);
  expect(renders[0].params.end).toBe(renders[1].params.start);
  expect(renders[1].params.end).toBe(renders[2].params.start);
  expect(renders[2].params.end).toBe(8);
});

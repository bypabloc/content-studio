import { expect, test } from '@playwright/test';

import { editorState, openEditor } from '../support/editor';

test('AC-7: deshacer y rehacer una eliminación conserva el proyecto', async ({ page }) => {
  const state = editorState();
  await openEditor(page, state);
  const workspace = page.getByRole('region', { name: 'Proyecto demo' });
  const clip = page.getByRole('button', { name: 'voz.wav: 0.0–8.0' });

  await clip.click();
  await workspace.press('Delete');
  await expect(clip).toHaveCount(0);
  await page.getByRole('button', { name: 'Deshacer' }).click();
  await expect(page.getByRole('button', { name: 'voz.wav: 0.0–8.0' })).toBeVisible();
  await page.getByRole('button', { name: 'Rehacer' }).click();
  await expect(page.getByRole('button', { name: 'voz.wav: 0.0–8.0' })).toHaveCount(0);
  await expect.poll(() => (state.project.doc.clips as unknown[]).length).toBe(0);
});

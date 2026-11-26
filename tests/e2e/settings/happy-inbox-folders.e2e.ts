import { expect, test } from '@playwright/test';
import { openApp, setDialogPick } from '../support/app';

interface Folder {
  id: number;
  path: string;
  kind: string;
  params: Record<string, unknown>;
  keep_awake: boolean;
  paused: boolean;
  created_at: string;
}

test('Ajustes > Integraciones: agregar una carpeta de entrada, pausarla y quitarla (AC-9)', async ({ page }) => {
  const folders: Folder[] = [];
  const { calls } = await openApp(page, {
    replies: (call) => {
      if (!call.path.startsWith('/inbox/folders')) return undefined;
      if (call.method === 'GET') return folders;
      if (call.method === 'POST' && call.path === '/inbox/folders') {
        const body = call.body as Omit<Folder, 'id' | 'paused' | 'created_at'>;
        const folder = { id: folders.length + 1, ...body, paused: false, created_at: '2026-11-25T00:00:00+00:00' };
        folders.push(folder);
        return folder;
      }
      if (call.path.endsWith('/pause')) {
        const folder = folders.find((item) => call.path === `/inbox/folders/${item.id}/pause`);
        if (folder) folder.paused = (call.body as { paused: boolean }).paused;
        return folder ?? {};
      }
      if (call.method === 'DELETE') {
        folders.splice(0, folders.length);
        return {};
      }
      return undefined;
    },
  });
  await page.evaluate(() => {
    location.hash = '#/settings';
  });

  await setDialogPick(page, ['C:/fake/entrada']);
  await page.getByRole('button', { name: 'Elegir carpeta' }).click();
  await expect(page.getByText('C:/fake/entrada')).toBeVisible();
  await page.getByRole('button', { name: 'Agregar carpeta' }).click();

  await expect(page.getByText('Activa')).toBeVisible();
  expect(calls.find((call) => call.method === 'POST' && call.path === '/inbox/folders')?.body).toMatchObject({
    path: 'C:/fake/entrada',
    kind: 'media.convert',
    params: { target: 'mp3' },
    keep_awake: true,
  });

  await page.getByRole('button', { name: 'Pausar carpeta' }).click();
  await expect(page.getByText('Pausada')).toBeVisible();

  page.once('dialog', (dialog) => void dialog.accept());
  await page.getByRole('button', { name: 'Quitar carpeta' }).click();
  await expect(page.getByText('No hay carpetas de entrada.')).toBeVisible();
});

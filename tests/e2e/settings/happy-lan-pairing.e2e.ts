import { expect, test, type Page } from '@playwright/test';
import { failCommand, openApp } from '../support/app';

interface LanSettings {
  enabled: boolean;
  address: string | null;
  port: number;
  running: boolean;
  url: string | null;
  addresses: string[];
  fingerprint: string | null;
}

const ENABLE = 'Permitir que otros equipos de mi red usen Content Studio';

/** La red local simulada: los ajustes cambian con PUT; emparejar agrega «celular»; revocar lo quita. */
async function openLan(page: Page) {
  let settings: LanSettings = {
    enabled: false,
    address: null,
    port: 41831,
    running: false,
    url: null,
    addresses: ['192.168.1.20', '10.0.0.5'],
    fingerprint: null,
  };
  const devices: { id: number; name: string }[] = [];
  const { calls } = await openApp(page, {
    replies: (call) => {
      if (call.path === '/lan/settings' && call.method === 'PUT') {
        const next = { ...settings, ...(call.body as Partial<LanSettings>) };
        const url = next.enabled && next.address ? `https://${next.address}:${next.port}` : null;
        settings = { ...next, running: next.enabled, url, fingerprint: next.enabled ? 'AB:CD:EF' : settings.fingerprint };
        return settings;
      }
      if (call.path === '/lan/settings') return settings;
      if (call.path === '/lan/devices') return devices;
      if (call.path === '/lan/pairing') {
        devices.push({ id: 1, name: 'celular' });
        return { pin: '654321', expires_in: 300 };
      }
      if (call.method === 'DELETE' && call.path === '/lan/devices/1') {
        devices.splice(0, devices.length);
        return {};
      }
      return undefined;
    },
  });
  await page.evaluate(() => {
    location.hash = '#/settings';
  });
  const toggle = page.getByRole('switch', { name: ENABLE });
  await toggle.scrollIntoViewIfNeeded();
  return { calls, toggle };
}

test('AC-10: activar la red local, elegir la dirección, emparejar un dispositivo y revocarlo', async ({ page }) => {
  const { calls, toggle } = await openLan(page);

  await toggle.click();
  await expect(page.getByText('https://192.168.1.20:41831')).toBeVisible();
  await expect(page.getByText('AB:CD:EF')).toBeVisible();
  await expect
    .poll(() => page.evaluate(() => (window as unknown as { __commands: string[] }).__commands.includes('set_lan_firewall')))
    .toBe(true);

  await page.getByRole('combobox', { name: 'Dirección en la red' }).click();
  await page.getByRole('option', { name: '10.0.0.5' }).click();
  await expect(page.getByText('https://10.0.0.5:41831')).toBeVisible();
  expect(calls.filter((call) => call.method === 'PUT' && call.path === '/lan/settings').map((call) => call.body)).toEqual([
    { enabled: true, address: '192.168.1.20' },
    { address: '10.0.0.5' },
  ]);

  await page.getByRole('button', { name: 'Emparejar dispositivo' }).click();
  await expect(page.getByText(/PIN: 654321 \(vence en \d+ s\)/)).toBeVisible();
  await expect(page.getByText('celular')).toBeVisible();

  page.once('dialog', (dialog) => void dialog.accept());
  await page.getByRole('button', { name: 'Revocar' }).click();
  await expect(page.getByText('No hay dispositivos emparejados.')).toBeVisible();
});

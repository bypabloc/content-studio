import { expect, test } from '@playwright/test';
import { openApp, type Replies } from '../support/app';
import { chooseFiles, cleanReplies, goToCleaner, newCleanState } from '../support/cleaner';

// Picos de la onda: el cliente los dibuja con WaveSurfer; sin ellos no hay onda ni regiones.
const PEAKS = Array.from({ length: 600 }, (_, i) => Math.abs(Math.sin(i / 9)) * (0.4 + 0.6 * Math.abs(Math.sin(i / 97))));

/** Un WAV mono de 16 bits y 8 kHz en silencio: basta para que el medio cargue y WaveSurfer emita «ready». */
function silentWav(seconds: number, rate = 8000): Buffer {
  const data = Buffer.alloc(seconds * rate * 2);
  const header = Buffer.alloc(44);
  header.write('RIFF', 0);
  header.writeUInt32LE(36 + data.length, 4);
  header.write('WAVE', 8);
  header.write('fmt ', 12);
  header.writeUInt32LE(16, 16);
  header.writeUInt16LE(1, 20);
  header.writeUInt16LE(1, 22);
  header.writeUInt32LE(rate, 24);
  header.writeUInt32LE(rate * 2, 28);
  header.writeUInt16LE(2, 32);
  header.writeUInt16LE(16, 34);
  header.write('data', 36);
  header.writeUInt32LE(data.length, 40);
  return Buffer.concat([header, data]);
}

test('los cortes se dibujan como regiones sobre la onda cuando el audio carga', async ({ page }) => {
  const state = newCleanState();
  const base = cleanReplies(state);
  const replies: Replies = (request) => (request.path === '/media/peaks' ? { peaks: PEAKS } : base(request));
  await openApp(page, { replies });
  // El audio llega de verdad: sin «ready» de WaveSurfer, las regiones no se dibujan.
  const media = silentWav(40);
  await page.route('**/files?path=*', (route) =>
    route.request().url().includes('nota') ? route.fulfill({ body: media, contentType: 'audio/wav' }) : route.fallback(),
  );
  await goToCleaner(page);

  await chooseFiles(page, ['C:/fake/in/nota.wav']);
  await page.getByRole('button', { name: 'Analizar', exact: true }).click();
  await page.getByRole('button', { name: 'Revisar', exact: true }).click();
  await expect(page.getByRole('button', { name: /^Corte 1:/ })).toBeVisible();

  // Una región por corte, con longitud (no marcadores de longitud cero).
  await expect(page.locator('[part^="region "]')).toHaveCount(2);
  await expect(page.locator('[part^="marker "]')).toHaveCount(0);
});

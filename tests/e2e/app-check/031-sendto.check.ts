import { existsSync } from 'node:fs';
import { join } from 'node:path';
import { expect, test } from '@playwright/test';

// «Enviar a» (spec 031, AC-6): con `app-check run --scenario=031-sendto --binary=<exe>` sobre la app instalada, los cinco
// accesos directos existen en la carpeta SendTo del usuario. Quitarlos al desinstalar se comprueba en la verificación final.
const SENDTO = join(process.env.APPDATA ?? '', 'Microsoft', 'Windows', 'SendTo');
const SHORTCUTS = ['Convertir a MP3', 'Normalizar', 'Limpiar silencios', 'Transcribir', 'Abrir en el Editor'];

test('031 AC-6: la instalación deja los cinco accesos directos de «Enviar a»', () => {
  for (const name of SHORTCUTS) {
    expect(existsSync(join(SENDTO, `Content Studio - ${name}.lnk`)), name).toBe(true);
  }
});

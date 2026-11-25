import { execFile } from 'node:child_process';
import { chromium, expect, test } from '@playwright/test';

const CDP = process.env.APP_CHECK_CDP ?? '';

/** Ejecuta un comando sin shell y devuelve su salida (spec 031). */
function output(file: string, args: string[]): Promise<string> {
  return new Promise((resolve, reject) => {
    execFile(file, args, (error, stdout) => (error ? reject(error) : resolve(stdout)));
  });
}

import { mkdirSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';

// Un WAV de silencio de 0,1 s: solo hace falta un archivo que exista para encolar (spec 031, AC-7).
function silentWav(path: string): void {
  const data = Buffer.alloc(3200);
  const header = Buffer.alloc(44);
  header.write('RIFF', 0);
  header.writeUInt32LE(36 + data.length, 4);
  header.write('WAVEfmt ', 8);
  header.writeUInt32LE(16, 16);
  header.writeUInt16LE(1, 20);
  header.writeUInt16LE(1, 22);
  header.writeUInt32LE(16000, 24);
  header.writeUInt32LE(32000, 28);
  header.writeUInt16LE(2, 32);
  header.writeUInt16LE(16, 34);
  header.write('data', 36);
  header.writeUInt32LE(data.length, 40);
  writeFileSync(path, Buffer.concat([header, data]));
}

// «Enviar a» (spec 031, AC-7): el acceso directo «Convertir a MP3» de la instalación manda los archivos a la app abierta.
test('031 AC-7: tres archivos con Convertir a MP3 encolan tres trabajos', async () => {
  const browser = await chromium.connectOverCDP(CDP);
  const page = browser.contexts()[0].pages()[0];
  await expect(page.getByRole('navigation', { name: 'Secciones' })).toBeVisible({ timeout: 90_000 });
  const dir = join(process.env.APP_CHECK_RUN ?? '.', 'sendto');
  mkdirSync(dir, { recursive: true });
  const files = ['uno', 'dos', 'tres'].map((name) => join(dir, `${name} con espacio.wav`));
  files.forEach(silentWav);
  const shortcut = join(process.env.APPDATA ?? '', 'Microsoft', 'Windows', 'SendTo', 'Content Studio - Convertir a MP3.lnk');
  const target = (
    await output('powershell', ['-NoProfile', '-Command', `$s = (New-Object -ComObject WScript.Shell).CreateShortcut('${shortcut}'); $s.TargetPath; $s.Arguments`])
  ).trim().split(/\r?\n/);
  const [exe, args] = [target[0], target[1]];
  await output(exe, [...args.split(' '), ...files]);
  await expect(page.getByText('3 archivos en la cola.')).toBeVisible({ timeout: 20_000 });
  await browser.close();
});

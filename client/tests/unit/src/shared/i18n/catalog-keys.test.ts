// @vitest-environment node
import { readdirSync, readFileSync, statSync } from 'node:fs';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { describe, expect, it } from 'vitest';
import catalog from '@messages/es.json';

const SRC = fileURLToPath(new URL('../../../../../src', import.meta.url));

function sourceFiles(dir: string): string[] {
  return readdirSync(dir).flatMap((name) => {
    const path = join(dir, name);
    if (statSync(path).isDirectory()) return sourceFiles(path);
    return /\.tsx?$/.test(name) ? [path] : [];
  });
}

const used = new Set(
  sourceFiles(SRC).flatMap((file) =>
    [...readFileSync(file, 'utf8').matchAll(/\bt\(\s*'([\w.]+)'/g)].map((match) => match[1]),
  ),
);

describe('catálogo es.json', () => {
  it('toda clave usada en src existe en el catálogo', () => {
    expect([...used].filter((key) => !(key in catalog))).toEqual([]);
  });

  // Hasta la etapa i18n (ciclo 3), que la reemplaza: las claves del server (`error.*`, `lint.*`) no las usa el client.
  it('ninguna clave del catálogo del client sobra', () => {
    const clientKeys = Object.keys(catalog).filter((key) => !/^(error|lint)\./.test(key));
    expect(clientKeys.filter((key) => !used.has(key))).toEqual([]);
  });
});

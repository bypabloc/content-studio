import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';

// Tokens que los componentes de klinikae usan y content-studio no definía (spec 008, D-6). Las sombras se
// guardan como `--ui-shadow*` (como en klinikae) y se exponen como utilidades `shadow-ui*` en `@theme inline`.
// Los de la última línea los necesitan las primitivas de shadcn y el AppShell.
const TOKENS = [
  'foreground-secondary',
  'primary-hover',
  'destructive-soft',
  'success',
  'success-soft',
  'accent-foreground',
  'ui-shadow',
  'ui-shadow-sm',
  'ui-shadow-lg',
  'popover',
  'popover-foreground',
  'secondary',
  'secondary-foreground',
  'sidebar',
  'sidebar-foreground',
  'sidebar-accent',
  'sidebar-border',
  'chart-1',
];

// Vitest no procesa CSS (devolvería vacío): se lee el archivo tal cual desde la raíz del client.
const css = readFileSync(resolve(import.meta.dirname, '../../../../src/styles/tokens.css'), 'utf-8');

/** El cuerpo de un bloque de CSS, p. ej. `:root { ... }` o `.dark { ... }`. */
function block(selector: string): string {
  const start = css.indexOf(`${selector} {`);
  if (start < 0) throw new Error(`no existe el bloque ${selector}`);
  return css.slice(start, css.indexOf('}', start));
}

/** Valor de una variable dentro de un bloque. */
function valueOf(scope: string, name: string): string {
  const match = new RegExp(`--${name}:\\s*([^;]+);`).exec(scope);
  if (!match) throw new Error(`falta --${name}`);
  return match[1].trim();
}

/** oklch(L C H) → luminancia relativa WCAG (solo colores opacos). */
function luminance(color: string): number {
  const match = /oklch\(\s*([\d.]+)\s+([\d.]+)\s+([\d.]+)\s*\)/.exec(color);
  if (!match) throw new Error(`no es oklch opaco: ${color}`);
  const [L, C, H] = [Number(match[1]), Number(match[2]), Number(match[3])];
  const a = C * Math.cos((H * Math.PI) / 180);
  const b = C * Math.sin((H * Math.PI) / 180);
  const l = (L + 0.3963377774 * a + 0.2158037573 * b) ** 3;
  const m = (L - 0.1055613458 * a - 0.0638541728 * b) ** 3;
  const s = (L - 0.0894841775 * a - 1.291485548 * b) ** 3;
  const clamp = (v: number) => Math.min(1, Math.max(0, v));
  const r = clamp(4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s);
  const g = clamp(-1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s);
  const bl = clamp(-0.0041960863 * l - 0.7034186147 * m + 1.707614701 * s);
  return 0.2126 * r + 0.7152 * g + 0.0722 * bl;
}

function contrast(a: string, b: string): number {
  const [hi, lo] = [luminance(a), luminance(b)].sort((x, y) => y - x);
  return (hi + 0.05) / (lo + 0.05);
}

describe.each([
  [':root', 'claro'],
  ['.dark', 'oscuro'],
])('tokens en %s (%s)', (selector) => {
  it.each(TOKENS)('define --%s', (token) => {
    expect(() => valueOf(block(selector), token)).not.toThrow();
  });
});

// El radio no depende del tema: vive solo en :root.
it('define --radius en :root', () => {
  expect(() => valueOf(block(':root'), 'radius')).not.toThrow();
});

describe('contraste AA de foreground-secondary sobre background', () => {
  it.each([
    [':root', 'claro'],
    ['.dark', 'oscuro'],
  ])('en %s (%s) llega a 4,5:1', (selector) => {
    const scope = block(selector);
    const ratio = contrast(valueOf(scope, 'foreground-secondary'), valueOf(scope, 'background'));

    expect(ratio).toBeGreaterThanOrEqual(4.5);
  });
});

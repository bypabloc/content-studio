import { describe, expect, it } from 'vitest';

// Las 27 primitivas copiadas de klinikae (spec 008, D-1 y D-3): cada una se importa y exporta algo.
const modules = import.meta.glob<Record<string, unknown>>('@/shared/components/shadcn/*.tsx', { eager: true });

describe('primitivas de shadcn', () => {
  it('son las 27 de klinikae', () => {
    expect(Object.keys(modules)).toHaveLength(27);
  });

  it.each(Object.keys(modules))('%s se importa y exporta al menos un componente', (path) => {
    const exported = Object.values(modules[path]);

    expect(exported.some((value) => typeof value === 'function' || typeof value === 'object')).toBe(true);
  });
});

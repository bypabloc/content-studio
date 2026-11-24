import { describe, expect, it } from 'vitest';
import packageJson from '../../../../package.json';
import { APP_VERSION } from '@/shared/version';

describe('APP_VERSION (spec 022, D-7)', () => {
  it('es la de client/package.json, la que escribe devtools version', () => {
    expect(APP_VERSION).toBe(packageJson.version);
    expect(APP_VERSION).toMatch(/^\d+\.\d+\.\d+$/);
  });
});

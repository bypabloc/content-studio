import { describe, expect, it } from 'vitest';

import { parseCube } from '@/features/editor/preview/lut';

describe('parseCube', () => {
  it('keeps red-fastest .cube samples in WebGL texture order', () => {
    const rows = ['0 0 0', '1 0 0', '0 1 0', '1 1 0', '0 0 1', '1 0 1', '0 1 1', '1 1 1'];

    expect(parseCube(`LUT_3D_SIZE 2\n${rows.join('\n')}`).data).toEqual(
      new Uint8Array([
        0, 0, 0, 255, 0, 0, 0, 255, 0, 255, 255, 0,
        0, 0, 255, 255, 0, 255, 0, 255, 255, 255, 255, 255,
      ]),
    );
  });

  it('rejects incomplete 3D cubes', () => {
    expect(() => parseCube('LUT_3D_SIZE 2\n0 0 0')).toThrow('Invalid 3D LUT');
  });

  it('reads titles and finite color domains', () => {
    const rows = Array(8).fill('0.5 0.5 0.5').join('\n');
    const parsed = parseCube(`TITLE "cinematic"\nDOMAIN_MIN 0.1 0.2 0.3\nDOMAIN_MAX 0.9 0.8 0.7\nLUT_3D_SIZE 2\n${rows}`);

    expect(parsed.domainMin).toEqual([0.1, 0.2, 0.3]);
    expect(parsed.domainMax).toEqual([0.9, 0.8, 0.7]);
  });

  it.each([
    'LUT_3D_SIZE 1',
    'LUT_3D_SIZE 65',
    'LUT_3D_SIZE 2\n2 0 0',
    'LUT_3D_SIZE 2\n' + '0 0 0\n'.repeat(9),
    'DOMAIN_MIN 0 0 NaN\nLUT_3D_SIZE 2',
    'DOMAIN_MIN 1 0 0\nLUT_3D_SIZE 2',
  ])('rejects invalid cube data: %s', (source) => {
    expect(() => parseCube(source)).toThrow('Invalid 3D LUT');
  });
});

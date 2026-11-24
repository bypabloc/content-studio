import { describe, expect, it } from 'vitest';

import { createTextStyle, TEXT_PRESETS } from '@/features/editor/text/presets';

describe('text presets', () => {
  it('provides the three title presets with valid raster dimensions and transparent strokes', () => {
    for (const preset of TEXT_PRESETS) {
      const style = createTextStyle(preset);
      expect(style.content).not.toHaveLength(0);
      expect(style.size).toBeGreaterThan(0);
      expect(style.max_width).toBeGreaterThan(0);
      expect(style.stroke.width).toBeGreaterThan(0);
    }
  });

  it('returns independent style objects for repeated presets', () => {
    const first = createTextStyle('lower-third');
    first.stroke.width = 99;
    expect(createTextStyle('lower-third').stroke.width).toBe(2);
  });
});

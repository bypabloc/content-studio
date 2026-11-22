import { describe, expect, it } from 'vitest';

import { BUILTIN_PRESETS, recommendedPreset } from '@/features/subtitles/presets';

describe('presets de subtítulos', () => {
  it('trae los cuatro presets con su modo (espejo de subtitles/styles.py)', () => {
    expect(Object.keys(BUILTIN_PRESETS).sort()).toEqual(['classic', 'karaoke', 'minimal', 'reels']);
    expect(BUILTIN_PRESETS.reels.mode).toBe('social');
    expect(BUILTIN_PRESETS.karaoke.mode).toBe('karaoke');
  });

  it('recomienda reels en vertical (aspecto ≤ 0,8) y classic en lo demás', () => {
    expect(recommendedPreset(9 / 16)).toBe('reels');
    expect(recommendedPreset(16 / 9)).toBe('classic');
  });
});

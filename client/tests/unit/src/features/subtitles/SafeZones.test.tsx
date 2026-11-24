import { cleanup, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';

import { SafeZones, zoneBox } from '@/features/subtitles/SafeZones';
import { t } from '@/shared/i18n/t';

describe('SafeZones', () => {
  afterEach(cleanup);

  it('gives the Reels zone its margins as percentages of the frame', () => {
    expect(zoneBox('reels')).toEqual({ top: 14, bottom: 35, left: 6, right: 6 });
  });

  it('draws the chosen zone over the preview and nothing without a zone', () => {
    const { unmount } = render(<SafeZones zone="reels" />);

    expect(screen.getByRole('group', { name: t('subtitles.zones.reels') })).toBeTruthy();
    unmount();

    render(<SafeZones zone={null} />);
    expect(screen.queryByRole('group')).toBeNull();
  });
});

import { cleanup, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';

import { Ruler } from '@/features/editor/Ruler';
import { t } from '@/shared/i18n/t';

afterEach(cleanup);

describe('Ruler', () => {
  it('muestra la regla accesible, los marcadores y el cabezal', () => {
    render(
      <Ruler
        duration={12}
        zoom={80}
        playhead={2}
        markers={[{ id: 'marker-1', t: 10, label: 'corte', color: '#f00' }]}
      />,
    );
    expect(screen.getByRole('group', { name: t('editor.timeline.ruler') })).toBeTruthy();
    expect(screen.getByText('corte')).toBeTruthy();
    expect(screen.getByRole('img', { name: t('editor.timeline.position') })).toBeTruthy();
  });
});

import { render } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { UIChartMarker } from '@/shared/components/atoms/UIChartMarker';

describe('UIChartMarker', () => {
  it('dibuja una cruz centrada en el punto, con su color', () => {
    const { container } = render(
      <svg>
        <UIChartMarker cx={10} cy={20} color="red" />
      </svg>,
    );

    const path = container.querySelector('path');
    expect(path?.getAttribute('d')).toBe('M6,16L14,24M6,24L14,16');
    expect(path?.getAttribute('stroke')).toBe('red');
  });

  it('sin coordenadas válidas no dibuja ninguna cruz', () => {
    const { container } = render(
      <svg>
        <UIChartMarker color="red" />
      </svg>,
    );

    expect(container.querySelector('path')).toBeNull();
  });
});

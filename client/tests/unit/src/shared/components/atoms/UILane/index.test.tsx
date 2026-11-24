import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { UILane } from '@/shared/components/atoms/UILane';

describe('UILane', () => {
  it('posiciona la pista y conserva sus atributos accesibles', () => {
    render(<UILane role="listitem" aria-label="Pista de voz" style={{ height: '80px' }} />);

    const lane = screen.getByRole('listitem', { name: 'Pista de voz' });
    expect(lane.style.position).toBe('relative');
    expect(lane.style.height).toBe('80px');
  });
});

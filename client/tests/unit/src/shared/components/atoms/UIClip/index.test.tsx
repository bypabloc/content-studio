import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { UIClip } from '@/shared/components/atoms/UIClip';

describe('UIClip', () => {
  it('posiciona un clip y expone su selección como botón', () => {
    render(<UIClip aria-label="Clip voz" aria-pressed style={{ left: '50px', width: '200px' }} />);

    const clip = screen.getByRole('button', { name: 'Clip voz' });
    expect(clip.getAttribute('aria-pressed')).toBe('true');
    expect(clip.style.position).toBe('absolute');
    expect(clip.style.left).toBe('50px');
    expect(clip.style.width).toBe('200px');
  });
});

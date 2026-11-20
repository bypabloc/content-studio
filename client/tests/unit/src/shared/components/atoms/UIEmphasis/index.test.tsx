import { cleanup, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';
import { UIEmphasis } from '@/shared/components/atoms/UIEmphasis';

afterEach(() => {
  cleanup();
});

describe('UIEmphasis (spec 010, D-6)', () => {
  it('pinta el texto en negrita, como un strong', () => {
    render(<UIEmphasis>sin gritar</UIEmphasis>);

    expect(screen.getByText('sin gritar').tagName).toBe('STRONG');
  });
});

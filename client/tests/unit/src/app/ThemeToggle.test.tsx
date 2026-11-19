import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { ThemeToggle } from '@/app/ThemeToggle';

afterEach(() => {
  cleanup();
});

describe('ThemeToggle', () => {
  it.each([
    ['light', 'dark'],
    ['dark', 'system'],
    ['system', 'light'],
  ] as const)('al pulsar pasa de %s a %s', (current, next) => {
    const onChange = vi.fn();
    render(<ThemeToggle mode={current} onChange={onChange} />);

    fireEvent.click(screen.getByRole('button'));

    expect(onChange).toHaveBeenCalledWith(next);
  });
});

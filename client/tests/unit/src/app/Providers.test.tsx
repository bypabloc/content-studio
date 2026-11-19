import { render, screen } from '@testing-library/react';
import { useQueryClient } from '@tanstack/react-query';
import { describe, expect, it } from 'vitest';
import { Providers } from '@/app/Providers';

function Probe() {
  const queryClient = useQueryClient();
  return <p>{queryClient ? 'con cliente' : 'sin cliente'}</p>;
}

describe('Providers', () => {
  it('da el QueryClient a los hijos', () => {
    render(
      <Providers>
        <Probe />
      </Providers>,
    );

    expect(screen.getByText('con cliente')).toBeTruthy();
  });
});

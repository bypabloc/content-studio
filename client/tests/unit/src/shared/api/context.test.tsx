import { renderHook } from '@testing-library/react';
import type { ReactNode } from 'react';
import { describe, expect, it } from 'vitest';
import { ApiProvider, useApi } from '@/shared/api/context';

const connection = { baseUrl: 'http://127.0.0.1:9000', token: 'tok' };

describe('ApiProvider y useApi', () => {
  it('da el cliente de la API a los hijos', () => {
    const wrapper = ({ children }: { children: ReactNode }) => (
      <ApiProvider connection={connection}>{children}</ApiProvider>
    );

    const { result } = renderHook(() => useApi(), { wrapper });

    expect(typeof result.current.get).toBe('function');
  });

  it('useApi fuera de ApiProvider falla con un mensaje claro', () => {
    expect(() => renderHook(() => useApi())).toThrow('useApi must be used inside ApiProvider');
  });
});

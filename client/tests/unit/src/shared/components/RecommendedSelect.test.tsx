import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import type { ComponentProps, ReactNode } from 'react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { ApiProvider } from '@/shared/api/context';
import { RecommendedSelect } from '@/shared/components/RecommendedSelect';

const connection = { baseUrl: 'http://127.0.0.1:9000', token: 'tok' };
const options = [
  { value: 'a', label: 'Alfa' },
  { value: 'b', label: 'Beta', recommended: true },
  { value: 'c', label: 'Gama' },
];

function reply(body: unknown) {
  return new Response(JSON.stringify(body), { status: 200 });
}

// Un cliente de consulta nuevo por render: así un "remontaje" vuelve a pedir la preferencia al server.
function mount(fetchMock: ReturnType<typeof vi.fn>, props: Partial<ComponentProps<typeof RecommendedSelect>> = {}) {
  vi.stubGlobal('fetch', fetchMock);
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      <ApiProvider connection={connection}>{children}</ApiProvider>
    </QueryClientProvider>
  );
  return render(<RecommendedSelect settingKey="select.demo" label="Demo" options={options} {...props} />, { wrapper });
}

describe('RecommendedSelect', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', undefined);
  });

  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
  });

  it('sin elección guardada preselecciona la recomendada, y solo ella lleva la estrella', async () => {
    mount(vi.fn(async () => reply({ key: 'select.demo', value: null })));

    const select = screen.getByRole('combobox', { name: 'Demo' }) as HTMLSelectElement;
    expect(select.value).toBe('b');
    const starred = [...select.options].filter((option) => option.textContent?.includes('★')).map((o) => o.value);
    expect(starred).toEqual(['b']);
  });

  it('al elegir otra la guarda en el server, y al volver a montar la preselecciona', async () => {
    const fetchMock = vi.fn(async (_url: string, init?: RequestInit) =>
      reply({ key: 'select.demo', value: init?.method === 'PUT' ? 'c' : null }),
    );
    const first = mount(fetchMock);
    fireEvent.change(screen.getByRole('combobox', { name: 'Demo' }), { target: { value: 'c' } });
    await waitFor(() =>
      expect(fetchMock).toHaveBeenCalledWith(
        'http://127.0.0.1:9000/settings/select.demo',
        expect.objectContaining({ method: 'PUT', body: '{"value":"c"}' }),
      ),
    );
    first.unmount();

    mount(vi.fn(async () => reply({ key: 'select.demo', value: 'c' })));

    await waitFor(() => expect((screen.getByRole('combobox', { name: 'Demo' }) as HTMLSelectElement).value).toBe('c'));
  });

  it('avisa al cambiar; una opción puede tener pista o estar deshabilitada', () => {
    const onChange = vi.fn();
    mount(vi.fn(async () => reply({ key: 'select.demo', value: null })), {
      onChange,
      options: [
        { value: 'a', label: 'Alfa', hint: 'la rápida' },
        { value: 'b', label: 'Beta', recommended: true },
        { value: 'c', label: 'Gama', disabled: true },
      ],
    });
    const select = screen.getByRole('combobox', { name: 'Demo' });

    fireEvent.change(select, { target: { value: 'a' } });

    expect(onChange).toHaveBeenCalledWith('a');
    expect(screen.getByRole('option', { name: 'Alfa' }).getAttribute('title')).toBe('la rápida');
    expect((screen.getByRole('option', { name: 'Gama' }) as HTMLOptionElement).disabled).toBe(true);
  });

  it('sin opciones, el selector queda vacío y no falla', () => {
    mount(vi.fn(async () => reply({ key: 'select.demo', value: null })), { options: [] });

    expect((screen.getByRole('combobox', { name: 'Demo' }) as HTMLSelectElement).options).toHaveLength(0);
  });

  it('sin opción recomendada, vale la primera', () => {
    mount(vi.fn(async () => reply({ key: 'select.demo', value: null })), {
      options: [
        { value: 'x', label: 'X' },
        { value: 'y', label: 'Y' },
      ],
    });

    expect((screen.getByRole('combobox', { name: 'Demo' }) as HTMLSelectElement).value).toBe('x');
  });

  it('si la elección guardada ya no existe, vuelve a la recomendada', async () => {
    mount(vi.fn(async () => reply({ key: 'select.demo', value: 'desaparecida' })));

    await waitFor(() => expect((screen.getByRole('combobox', { name: 'Demo' }) as HTMLSelectElement).value).toBe('b'));
  });
});

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { cleanup, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import type { ComponentProps, ReactNode } from 'react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { ApiProvider } from '@/shared/api/context';
import { UIRecommendedSelect } from '@/shared/components/molecules/UIRecommendedSelect';

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
function mount(fetchMock: ReturnType<typeof vi.fn>, props: Partial<ComponentProps<typeof UIRecommendedSelect>> = {}) {
  vi.stubGlobal('fetch', fetchMock);
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      <ApiProvider connection={connection}>{children}</ApiProvider>
    </QueryClientProvider>
  );
  const result = render(<UIRecommendedSelect settingKey="select.demo" label="Demo" options={options} {...props} />, {
    wrapper,
  });
  return { ...result, queryClient };
}

// El selector es un combobox (UISelect sobre Base UI) y su Picker se carga aparte: por eso se espera con findByRole.
async function combobox(): Promise<HTMLInputElement> {
  return (await screen.findByRole('combobox', { name: 'Demo' })) as HTMLInputElement;
}

describe('UIRecommendedSelect', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', undefined);
  });

  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
  });

  it('sin elección guardada preselecciona la recomendada, y solo ella lleva la estrella', async () => {
    mount(vi.fn(async () => reply({ key: 'select.demo', value: null })));

    expect((await combobox()).value).toBe('★ Beta');
    await userEvent.click(await combobox());
    const starred = screen
      .getAllByRole('option')
      .map((option) => option.textContent ?? '')
      .filter((text) => text.includes('★'));
    expect(starred).toHaveLength(1);
    expect(starred[0]).toContain('Beta');
  });

  it('al elegir otra la guarda en el server, y al volver a montar la preselecciona', async () => {
    const fetchMock = vi.fn(async (_url: string, init?: RequestInit) =>
      reply({ key: 'select.demo', value: init?.method === 'PUT' ? 'c' : null }),
    );
    const first = mount(fetchMock);
    await userEvent.click(await combobox());
    await userEvent.click(screen.getByRole('option', { name: 'Gama' }));
    await waitFor(() =>
      expect(fetchMock).toHaveBeenCalledWith(
        'http://127.0.0.1:9000/settings/select.demo',
        expect.objectContaining({ method: 'PUT', body: '{"value":"c"}' }),
      ),
    );
    first.unmount();

    mount(vi.fn(async () => reply({ key: 'select.demo', value: 'c' })));

    await waitFor(async () => expect((await combobox()).value).toBe('Gama'));
  });

  it('avisa al cambiar; una opción puede tener pista o estar deshabilitada', async () => {
    const onChange = vi.fn();
    mount(vi.fn(async () => reply({ key: 'select.demo', value: null })), {
      onChange,
      options: [
        { value: 'a', label: 'Alfa', hint: 'la rápida' },
        { value: 'b', label: 'Beta', recommended: true },
        { value: 'c', label: 'Gama', disabled: true },
      ],
    });

    await userEvent.click(await combobox());

    expect(screen.getByText('la rápida')).toBeTruthy();
    expect(screen.getByRole('option', { name: /Gama/ }).getAttribute('aria-disabled')).toBe('true');
    await userEvent.click(screen.getByRole('option', { name: /Alfa/ }));
    expect(onChange).toHaveBeenCalledWith('a');
  });

  it('con beforeChange que responde que no, la elección no cambia', async () => {
    const onChange = vi.fn();
    const beforeChange = vi.fn(async () => false);
    mount(vi.fn(async () => reply({ key: 'select.demo', value: null })), { onChange, beforeChange });

    await userEvent.click(await combobox());
    await userEvent.click(screen.getByRole('option', { name: 'Gama' }));

    await waitFor(() => expect(beforeChange).toHaveBeenCalledWith('c'));
    expect(onChange).not.toHaveBeenCalled();
    expect((await combobox()).value).toBe('★ Beta');
  });

  it('el nombre del selector se ve como etiqueta asociada, no solo como aria-label', async () => {
    mount(vi.fn(async () => reply({ key: 'select.demo', value: null })));

    const label = screen.getByText('Demo');
    expect(label.tagName).toBe('LABEL');
    expect((label as HTMLLabelElement).control).toBe(await combobox());
  });

  it('sin opciones, el selector queda deshabilitado y no falla', async () => {
    mount(vi.fn(async () => reply({ key: 'select.demo', value: null })), { options: [] });

    expect((await combobox()).disabled).toBe(true);
  });

  it('sin opción recomendada, vale la primera', async () => {
    mount(vi.fn(async () => reply({ key: 'select.demo', value: null })), {
      options: [
        { value: 'x', label: 'X' },
        { value: 'y', label: 'Y' },
      ],
    });

    expect((await combobox()).value).toBe('X');
  });

  it('si la elección guardada ya no existe, vuelve a la recomendada', async () => {
    const { queryClient } = mount(vi.fn(async () => reply({ key: 'select.demo', value: 'desaparecida' })));

    // La recomendada ya está por defecto: sin esperar la respuesta del server, la prueba no diría nada.
    await waitFor(() =>
      expect(queryClient.getQueryData(['settings', 'select.demo'])).toEqual({ key: 'select.demo', value: 'desaparecida' }),
    );
    expect((await combobox()).value).toBe('★ Beta');
  });
});

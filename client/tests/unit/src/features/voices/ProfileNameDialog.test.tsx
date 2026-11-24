import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { ProfileNameDialog } from '@/features/voices/ProfileNameDialog';
import { t } from '@/shared/i18n/t';

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

const BASE = {
  open: true,
  onOpenChange: () => {},
  title: 'Nuevo perfil',
  description: 'Un perfil guarda una referencia por estilo.',
  confirmLabel: 'Crear',
  value: '',
  onChange: () => {},
  pending: false,
  onSubmit: () => {},
};

describe('ProfileNameDialog (spec 010, D-6)', () => {
  it('escribir en el campo entrega el nombre nuevo', () => {
    const onChange = vi.fn();
    render(<ProfileNameDialog {...BASE} onChange={onChange} />);

    fireEvent.change(screen.getByRole('textbox', { name: t('voices.name') }), { target: { value: 'Voz nueva' } });

    expect(onChange).toHaveBeenCalledWith('Voz nueva');
  });

  it('un nombre solo con espacios no se puede enviar', () => {
    render(<ProfileNameDialog {...BASE} value="   " />);

    expect((screen.getByRole('button', { name: 'Crear' }) as HTMLButtonElement).disabled).toBe(true);
  });

  it('con nombre, confirmar llama a onSubmit', () => {
    const onSubmit = vi.fn();
    render(<ProfileNameDialog {...BASE} value="Voz" onSubmit={onSubmit} />);

    fireEvent.click(screen.getByRole('button', { name: 'Crear' }));

    expect(onSubmit).toHaveBeenCalledTimes(1);
  });

  it('muestra el error de la API junto al campo', () => {
    render(<ProfileNameDialog {...BASE} value="Voz" error="Ya existe un perfil con ese nombre." />);

    expect(screen.getByText('Ya existe un perfil con ese nombre.')).toBeTruthy();
  });
});

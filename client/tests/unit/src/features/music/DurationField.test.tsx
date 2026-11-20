import { cleanup, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { useState, type ComponentProps } from 'react';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { DurationField, type MatchSource } from '@/features/music/DurationField';
import { t } from '@/shared/i18n/t';

const narration: MatchSource = { id: 'n1', label: 'Narración de prueba', starred: true, duration: 47.3 };
const longNarration: MatchSource = { id: 'n2', label: 'Narración larga', starred: false, duration: 300 };

type Props = ComponentProps<typeof DurationField>;

/** El campo con su valor en estado, como en la pantalla: así el texto muestra lo que se eligió. */
function Harness({ initial = 0, onChange, ...props }: Omit<Props, 'value' | 'onChange'> & { initial?: number; onChange: (s: number) => void }) {
  const [value, setValue] = useState(initial);
  return (
    <DurationField
      {...props}
      value={value}
      onChange={(seconds) => {
        setValue(seconds);
        onChange(seconds);
      }}
    />
  );
}

function renderField(overrides: Partial<Props> = {}) {
  const onChange = vi.fn();
  const onTailChange = vi.fn();
  const pickMediaDuration = vi.fn((): Promise<number | null> => Promise.resolve(null));
  render(
    <Harness
      max={600}
      tail={2}
      matchSources={[narration]}
      onTailChange={onTailChange}
      pickMediaDuration={pickMediaDuration}
      onChange={onChange}
      {...overrides}
    />,
  );
  return { onChange, onTailChange, pickMediaDuration };
}

const durationInput = () => screen.getByRole('textbox', { name: t('music.duration.label') });

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe('DurationField (spec 011, D-4, AC-6)', () => {
  it('WHEN se elige «Igualar a narración» con una narración de 47,3 s y una cola de 2 s THEN el campo muestra 00:49.3', async () => {
    const user = userEvent.setup();
    const { onChange } = renderField();

    await user.click(screen.getByRole('button', { name: t('music.duration.match') }));
    await user.click(screen.getByRole('button', { name: /Narración de prueba/ }));

    expect(onChange).toHaveBeenCalledWith(49.3);
    expect((durationInput() as HTMLInputElement).value).toBe('00:49.3');
  });

  it('WHEN la duración igualada pasa el máximo del motor THEN muestra duration_over_max y no cambia el valor', async () => {
    const user = userEvent.setup();
    const { onChange } = renderField({ max: 240, matchSources: [longNarration] });

    await user.click(screen.getByRole('button', { name: t('music.duration.match') }));
    await user.click(screen.getByRole('button', { name: /Narración larga/ }));

    expect(screen.queryByText(t('error.duration_over_max', { max: 240 }))).not.toBeNull();
    expect(onChange).not.toHaveBeenCalled();
  });

  it('WHEN se elige el preset de 60 s THEN la duración es 60', async () => {
    const user = userEvent.setup();
    const { onChange } = renderField();

    await user.click(screen.getByRole('button', { name: t('music.duration.preset.seconds', { n: 60 }) }));

    expect(onChange).toHaveBeenCalledWith(60);
  });

  it('WHEN el máximo es 2 min THEN el preset de 3 min está deshabilitado', () => {
    renderField({ max: 120 });

    expect((screen.getByRole('button', { name: t('music.duration.preset.minutes', { n: 3 }) }) as HTMLButtonElement).disabled).toBe(true);
  });

  it('WHEN se escribe mm:ss y se sale del campo THEN la duración es esa', async () => {
    const user = userEvent.setup();
    const { onChange } = renderField();

    await user.type(durationInput(), '01:15.5');
    await user.tab();

    expect(onChange).toHaveBeenCalledWith(75.5);
  });

  it('WHEN el texto no es un reloj THEN muestra el error y no cambia el valor', async () => {
    const user = userEvent.setup();
    const { onChange } = renderField();

    await user.type(durationInput(), 'abc');
    await user.tab();

    expect(screen.queryByText(t('music.duration.invalid'))).not.toBeNull();
    expect(onChange).not.toHaveBeenCalled();
  });

  it('WHEN se iguala a un archivo THEN usa su duración más la cola', async () => {
    const user = userEvent.setup();
    const { onChange, pickMediaDuration } = renderField();
    pickMediaDuration.mockResolvedValueOnce(125);

    await user.click(screen.getByRole('button', { name: t('music.duration.match') }));
    await user.click(screen.getByRole('button', { name: t('music.duration.matchFile') }));

    expect(onChange).toHaveBeenCalledWith(127);
  });

  it('WHEN se cancela el diálogo de archivo THEN no cambia nada', async () => {
    const user = userEvent.setup();
    const { onChange } = renderField();

    await user.click(screen.getByRole('button', { name: t('music.duration.match') }));
    await user.click(screen.getByRole('button', { name: t('music.duration.matchFile') }));

    expect(onChange).not.toHaveBeenCalled();
  });

  it('WHEN no hay narraciones terminadas THEN el menú lo dice', async () => {
    const user = userEvent.setup();
    renderField({ matchSources: [] });

    await user.click(screen.getByRole('button', { name: t('music.duration.match') }));

    expect(screen.queryByText(t('music.duration.noSources'))).not.toBeNull();
  });

  it('WHEN se cambia la cola THEN se avisa con el nuevo valor', async () => {
    const user = userEvent.setup();
    const { onTailChange } = renderField();

    await user.click(screen.getByRole('button', { name: t('music.duration.match') }));
    const tail = screen.getByRole('spinbutton', { name: t('music.duration.matchTail') });
    await user.clear(tail);
    await user.type(tail, '5');

    expect(onTailChange).toHaveBeenLastCalledWith(5);
  });
});

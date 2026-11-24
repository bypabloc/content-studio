import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { RecordControls } from '@/features/recording/RecordControls';
import { t } from '@/shared/i18n/t';

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

const LEVELS = { peak: -4, rms: -15 };

describe('RecordControls (spec 010, D-6)', () => {
  it('antes de grabar ofrece grabar; grabando ofrece parar', () => {
    const onToggle = vi.fn();
    const { rerender } = render(
      <RecordControls recording={false} levels={LEVELS} elapsed={0} target={{ min: 10, max: 12 }} onToggle={onToggle} />,
    );

    fireEvent.click(screen.getByRole('button', { name: t('voices.record.start') }));
    expect(onToggle).toHaveBeenCalledTimes(1);

    rerender(<RecordControls recording levels={LEVELS} elapsed={0} target={{ min: 10, max: 12 }} onToggle={onToggle} />);
    expect(screen.getByRole('button', { name: t('voices.record.stop') })).toBeTruthy();
  });

  it('el reloj dice si la toma va dentro del rango objetivo y, si se pasa, que está fuera', () => {
    const { rerender } = render(
      <RecordControls recording levels={LEVELS} elapsed={11.2} target={{ min: 10, max: 12 }} onToggle={() => {}} />,
    );
    expect(screen.getByText(t('voices.record.in_range'))).toBeTruthy();

    rerender(<RecordControls recording levels={LEVELS} elapsed={13} target={{ min: 10, max: 12 }} onToggle={() => {}} />);
    expect(screen.getByText(t('voices.record.out_of_range'))).toBeTruthy();
  });

  it('muestra el medidor del nivel de entrada', () => {
    render(<RecordControls recording={false} levels={LEVELS} elapsed={0} target={{ min: 10, max: 12 }} onToggle={() => {}} />);

    expect(screen.getByRole('meter', { name: t('voices.record.level') })).toBeTruthy();
  });
});

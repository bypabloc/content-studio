import { cleanup, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';
import { Teleprompter } from '@/features/recording/Teleprompter';
import { t } from '@/shared/i18n/t';

afterEach(() => {
  cleanup();
});

const NEUTRAL = {
  style: 'neutral',
  optional: false,
  text: 'Hoy quiero contarte.',
  marked: 'Hoy quiero / contarte. ↘',
  duration: { min: 10, max: 12 },
  ppm: 150,
};

describe('Teleprompter (spec 010, D-6)', () => {
  it('muestra el estilo, su guion marcado, la duración objetivo, el ritmo y la leyenda de la notación', () => {
    render(<Teleprompter style={NEUTRAL} step={1} total={12} />);

    expect(screen.getByText(t('label.narration.style.neutral'))).toBeTruthy();
    expect(screen.getByText(t('voices.record.step', { n: 1, total: 12 }))).toBeTruthy();
    expect(screen.getByText('Hoy quiero / contarte. ↘')).toBeTruthy();
    expect(screen.getByText(t('voices.record.duration', { min: 10, max: 12 }))).toBeTruthy();
    expect(screen.getByText(t('voices.record.ppm', { ppm: 150 }))).toBeTruthy();
    expect(screen.getByText(t('voices.record.notation'))).toBeTruthy();
  });

  it('un estilo opcional lo dice, y sin ritmo fijo no muestra los ppm', () => {
    render(
      <Teleprompter
        style={{ ...NEUTRAL, style: 'whisper', optional: true, ppm: null, duration: { min: 7, max: 9 } }}
        step={13}
        total={13}
      />,
    );

    expect(screen.getByText(t('voices.record.optional'))).toBeTruthy();
    expect(screen.queryByText(t('voices.record.ppm', { ppm: 150 }))).toBeNull();
  });

  it('la negrita del guion (entre dobles asteriscos) se pinta en negrita y lo demás queda igual', () => {
    render(<Teleprompter style={{ ...NEUTRAL, marked: 'Hoy **quiero** contarte. ↘' }} step={1} total={12} />);

    expect(screen.getByText('quiero').tagName).toBe('STRONG');
    expect(screen.getByText(/Hoy/).textContent).toContain('Hoy');
    expect(screen.queryByText(/\*\*/)).toBeNull();
  });
});

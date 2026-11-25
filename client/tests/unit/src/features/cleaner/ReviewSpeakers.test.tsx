import { cleanup, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';

import { ReviewSpeakers, speakerUnderline } from '@/features/cleaner/ReviewSpeakers';
import { t } from '@/shared/i18n/t';

const speakers = {
  SPEAKER_00: { name: 'Ana', color: '#2563eb' },
  SPEAKER_01: { name: 'Luis', color: '#dc2626' },
};

afterEach(() => {
  cleanup();
});

describe('speakerUnderline', () => {
  it('subraya la palabra con el color de su hablante (AC-8)', () => {
    expect(speakerUnderline({ speaker: 'SPEAKER_00' }, speakers)).toEqual({ borderBottom: '3px solid #2563eb' });
  });

  it('no subraya una palabra sin hablante, con un hablante que no está en el mapa o sin mapa', () => {
    expect(speakerUnderline({ speaker: null }, speakers)).toBeUndefined();
    expect(speakerUnderline({ speaker: 'SPEAKER_09' }, speakers)).toBeUndefined();
    expect(speakerUnderline({ speaker: 'SPEAKER_00' }, undefined)).toBeUndefined();
  });
});

describe('ReviewSpeakers', () => {
  it('muestra el título y un chip por hablante con su nombre (AC-8)', () => {
    render(<ReviewSpeakers speakers={speakers} />);

    expect(screen.getByText(t('cleaner.review.speakers'))).toBeTruthy();
    expect(screen.getByText('Ana')).toBeTruthy();
    expect(screen.getByText('Luis')).toBeTruthy();
  });
});

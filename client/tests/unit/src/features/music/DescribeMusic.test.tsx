import { cleanup, fireEvent, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { DescribeMusic } from '@/features/music/DescribeMusic';
import { t } from '@/shared/i18n/t';

import { api, renderWith, STATUS } from '../../../assistant-harness';

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe('DescribeMusic (spec 021, D-5)', () => {
  it('WHEN se describe en español y se usa la sugerencia THEN llena el texto libre', async () => {
    const onApply = vi.fn();
    const sent: unknown[] = [];
    renderWith(
      <DescribeMusic onApply={onApply} />,
      api({
        '/llm/status': STATUS,
        'POST /jobs': (body: unknown) => {
          sent.push(body);
          return { id: 9 };
        },
        '/jobs': [{ id: 9, kind: 'llm.music_caption', status: 'done' }],
        '/llm/jobs/9/result': { caption: 'soft piano, rain, no vocals', key: 'C Major', bpm: 80, time_signature: '4' },
      }),
    );

    await userEvent.type(await screen.findByRole('textbox', { name: t('llm.describe.label') }), 'piano y lluvia');
    fireEvent.click(screen.getByRole('button', { name: t('llm.button.describe') }));
    fireEvent.click(await screen.findByRole('button', { name: t('llm.describe.use') }));

    expect(sent[0]).toEqual({ kind: 'llm.music_caption', params: { description: 'piano y lluvia' } });
    expect(onApply).toHaveBeenCalledWith({ caption: 'soft piano, rain, no vocals', key: 'C Major', bpm: 80, timeSignature: '4' });
  });

  it('WHEN el asistente está apagado THEN no aparece', async () => {
    const { container } = renderWith(<DescribeMusic onApply={() => {}} />, api({ '/llm/status': { ...STATUS, enabled: false } }));
    await new Promise((resolve) => setTimeout(resolve, 20));
    expect(container.textContent).toBe('');
  });
});

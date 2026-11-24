import { cleanup, fireEvent, screen, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { clock, PublishTab } from '@/features/library/PublishTab';
import type { LibraryItem } from '@/features/library/types';
import { t } from '@/shared/i18n/t';

import { api, renderWith, STATUS } from '../../../assistant-harness';

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

const item = { id: 7, name: 'demo.mp4', path: 'demo.mp4', media_type: 'video' } as unknown as LibraryItem;
const saved = {
  platforms: {
    youtube: {
      titles: ['Cómo vender más', 'Tres ideas', 'Guía rápida'],
      description: 'Un video.',
      hashtags: ['#ventas', '#pymes'],
      chapters: [
        { t: 0, title: 'Inicio' },
        { t: 65, title: 'Primera idea' },
      ],
    },
  },
};

describe('PublishTab (spec 021, D-5)', () => {
  it('clock da el formato de los capítulos', () => {
    expect([clock(0), clock(65), clock(750.4)]).toEqual(['0:00', '1:05', '12:30']);
  });

  it('WHEN ya se generó THEN muestra los campos y cada uno se copia', async () => {
    const writeText = vi.fn(async () => {});
    vi.stubGlobal('navigator', { ...navigator, clipboard: { writeText } });
    renderWith(<PublishTab item={item} />, api({ '/llm/status': STATUS, '/library/7/publish': saved }));

    expect(await screen.findByText('Cómo vender más')).toBeTruthy();
    expect(screen.getByText('#ventas #pymes')).toBeTruthy();
    fireEvent.click(screen.getByRole('button', { name: `${t('action.copy')}: ${t('llm.publish.chapters')}` }));

    expect(writeText).toHaveBeenCalledWith('0:00 Inicio\n1:05 Primera idea');
  });

  it('WHEN se eligen plataformas y se genera THEN encola llm.publish con ellas', async () => {
    const sent: unknown[] = [];
    renderWith(
      <PublishTab item={item} />,
      api({
        '/llm/status': STATUS,
        'POST /jobs': (body: unknown) => {
          sent.push(body);
          return { id: 2 };
        },
        '/jobs': [{ id: 2, kind: 'llm.publish', status: 'done' }],
        '/llm/jobs/2/result': saved,
      }),
    );

    fireEvent.click(await screen.findByRole('checkbox', { name: t('llm.platform.reels') }));
    fireEvent.click(screen.getByRole('checkbox', { name: t('llm.platform.youtube') }));
    fireEvent.click(screen.getByRole('button', { name: t('llm.button.publish') }));

    await waitFor(() => expect(sent).toEqual([{ kind: 'llm.publish', params: { item_id: 7, platforms: ['reels'] } }]));
    expect(await screen.findByText('Tres ideas')).toBeTruthy();
  });
});

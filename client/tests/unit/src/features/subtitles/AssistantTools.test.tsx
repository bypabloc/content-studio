import { cleanup, fireEvent, screen, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { AssistantTools } from '@/features/subtitles/AssistantTools';
import { t } from '@/shared/i18n/t';

import { api, renderWith, STATUS } from '../../../assistant-harness';

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

const base = {
  '/llm/status': STATUS,
  '/llm/languages': [{ code: 'en', name: 'English', recommended: true }, { code: 'pt', name: 'Português', recommended: false }],
  '/settings/select.llm.language': { key: 'select.llm.language', value: 'pt' },
  '/settings/subtitles.glossary': { key: 'subtitles.glossary', value: ['Klinikae'] },
};

describe('AssistantTools (spec 021, D-5)', () => {
  it('WHEN se corrige con el glosario y se aplica THEN guarda antes, encola y aplica lo elegido', async () => {
    const onBeforeRun = vi.fn(async () => {});
    const onApplied = vi.fn();
    const sent: unknown[] = [];
    const fetchMock = api({
      ...base,
      'POST /jobs': (body: unknown) => {
        sent.push(body);
        return { id: 4 };
      },
      '/jobs': [{ id: 4, kind: 'llm.subtitles_correct', status: 'done' }],
      '/llm/jobs/4/result': { cues: [{ id: 1, original: 'Hola Clinicae', text: 'Hola Klinikae', review: false }] },
      'POST /llm/subtitles/2/apply': (body: unknown) => ({ cues: [], echo: body }),
    });
    renderWith(<AssistantTools projectId={2} onBeforeRun={onBeforeRun} onApplied={onApplied} />, fetchMock);

    fireEvent.click(await screen.findByRole('button', { name: t('llm.button.correct') }));
    fireEvent.click(await screen.findByRole('button', { name: t('llm.apply_selected') }));

    await waitFor(() => expect(onApplied).toHaveBeenCalled());
    expect(onBeforeRun).toHaveBeenCalled();
    expect(sent[0]).toEqual({ kind: 'llm.subtitles_correct', params: { project_id: 2, glossary: ['Klinikae'] } });
    expect(onApplied.mock.calls[0][0].echo).toEqual({ job_id: 4, accepted: [1] });
  });

  it('WHEN se traduce THEN encola el idioma elegido y la pista se acepta entera', async () => {
    const sent: unknown[] = [];
    const onApplied = vi.fn();
    renderWith(
      <AssistantTools projectId={2} onBeforeRun={async () => {}} onApplied={onApplied} />,
      api({
        ...base,
        'POST /jobs': (body: unknown) => {
          sent.push(body);
          return { id: 8 };
        },
        '/jobs': [{ id: 8, kind: 'llm.subtitles_translate', status: 'done' }],
        '/llm/jobs/8/result': { language: 'pt', cues: [{ id: 1, text: 'Olá', original: 'Hola', flag: 'too_long' }] },
        'POST /llm/subtitles/2/apply': (body: unknown) => ({ echo: body }),
      }),
    );

    fireEvent.click(await screen.findByRole('button', { name: t('llm.button.translate') }));
    expect(await screen.findByText(t('llm.subtitles.flag.too_long'))).toBeTruthy();
    fireEvent.click(screen.getByRole('button', { name: t('llm.subtitles.accept_track') }));

    await waitFor(() => expect(onApplied).toHaveBeenCalled());
    expect(sent[0]).toEqual({ kind: 'llm.subtitles_translate', params: { project_id: 2, language: 'pt' } });
    expect(onApplied.mock.calls[0][0].echo).toEqual({ job_id: 8, accepted: null });
  });

  it('WHEN se piden palabras clave THEN las muestra con su emoji', async () => {
    renderWith(
      <AssistantTools projectId={2} onBeforeRun={async () => {}} onApplied={() => {}} />,
      api({
        ...base,
        'POST /jobs': { id: 5 },
        '/jobs': [{ id: 5, kind: 'llm.subtitles_keywords', status: 'done' }],
        '/llm/jobs/5/result': { cues: [{ id: 1, word: 'rápido', emoji: '🚀' }] },
      }),
    );

    fireEvent.click(await screen.findByRole('button', { name: t('llm.button.keywords') }));

    expect(await screen.findByText('rápido 🚀')).toBeTruthy();
  });

  it('WHEN una palabra no trae emoji y aplicar falla THEN muestra la palabra sola y no cambia el documento', async () => {
    const onApplied = vi.fn();
    const failing = api({
      ...base,
      '/llm/languages': { unexpected: true },
      'POST /jobs': { id: 6 },
      '/jobs': [{ id: 6, kind: 'llm.subtitles_keywords', status: 'done' }],
      '/llm/jobs/6/result': { cues: [{ id: 1, word: 'vende', emoji: null }] },
    });
    renderWith(<AssistantTools projectId={2} onBeforeRun={async () => {}} onApplied={onApplied} />, failing);

    fireEvent.click(await screen.findByRole('button', { name: t('llm.button.keywords') }));
    expect(await screen.findByText('vende')).toBeTruthy();
    fireEvent.click(screen.getByRole('button', { name: t('llm.apply_selected') }));

    await waitFor(() => expect(failing.mock.calls.some(([url]) => String(url).endsWith('/apply'))).toBe(true));
    expect(onApplied).not.toHaveBeenCalled();
  });

  it('WHEN el asistente está apagado THEN no aparece', async () => {
    const { container } = renderWith(
      <AssistantTools projectId={2} onBeforeRun={async () => {}} onApplied={() => {}} />,
      api({ ...base, '/llm/status': { ...STATUS, enabled: false } }),
    );
    await new Promise((resolve) => setTimeout(resolve, 20));
    expect(container.textContent).toBe('');
  });
});

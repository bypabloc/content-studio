import { cleanup, fireEvent, screen, waitFor } from '@testing-library/react';
import { useState } from 'react';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { replaceParagraph, ScriptReview } from '@/features/narration/ScriptReview';
import { t } from '@/shared/i18n/t';

import { api, calls, renderWith, STATUS } from '../../../assistant-harness';

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

const paragraph = { index: 1, original: 'Tienes 24 horas.', revised: 'Tienes veinticuatro horas.', changes: [] };

function Harness() {
  const [text, setText] = useState('Hola.\n\nTienes 24 horas.');
  return (
    <>
      <ScriptReview text={text} onChange={setText} />
      <output>{text}</output>
    </>
  );
}

describe('ScriptReview (spec 021, AC-9)', () => {
  it('replaceParagraph cambia el párrafo por su índice o, si se movió, por su texto', () => {
    expect(replaceParagraph('Hola.\n\nTienes 24 horas.', paragraph)).toBe('Hola.\n\nTienes veinticuatro horas.');
    expect(replaceParagraph('Tienes 24 horas.\n\nHola.', paragraph)).toBe('Tienes veinticuatro horas.\n\nHola.');
    expect(replaceParagraph('Otro texto.', paragraph)).toBe('Otro texto.');
  });

  it('WHEN se revisa y se acepta THEN el editor queda con el texto aceptado', async () => {
    const fetchMock = api({
      '/llm/status': STATUS,
      'POST /jobs': { id: 3 },
      '/jobs': [{ id: 3, kind: 'llm.script_review', status: 'done' }],
      '/llm/jobs/3/result': { paragraphs: [paragraph], discarded: [] },
    });
    renderWith(<Harness />, fetchMock);

    fireEvent.click(await screen.findByRole('button', { name: t('llm.button.review') }));
    fireEvent.click(await screen.findByRole('button', { name: t('llm.accept') }));

    await waitFor(() => expect(screen.getByRole('status').textContent).toBe('Hola.\n\nTienes veinticuatro horas.'));
    expect(calls(fetchMock)).toContain('POST /jobs');
  });
});

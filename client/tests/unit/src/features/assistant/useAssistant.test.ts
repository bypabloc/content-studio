import { act, renderHook, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { assistantReady, useAssistantTask } from '@/features/assistant/useAssistant';

import { api, calls, STATUS, wrapperFor } from '../../../assistant-harness';

afterEach(() => vi.unstubAllGlobals());

function task(fetchMock: ReturnType<typeof api>) {
  return renderHook(() => useAssistantTask<{ caption: string }>('llm.music_caption'), { wrapper: wrapperFor(fetchMock) });
}

describe('useAssistantTask (spec 021, D-5)', () => {
  it('WHEN el trabajo termina THEN pide la propuesta y la devuelve', async () => {
    const fetchMock = api({
      'POST /jobs': { id: 5 },
      '/jobs': [{ id: 5, kind: 'llm.music_caption', status: 'done' }],
      '/llm/jobs/5/result': { caption: 'soft piano, no vocals' },
    });
    const { result } = task(fetchMock);

    act(() => result.current.run({ description: 'piano' }));

    await waitFor(() => expect(result.current.result?.caption).toBe('soft piano, no vocals'));
    expect(result.current.busy).toBe(false);
    expect(result.current.jobId).toBe(5);
    expect(calls(fetchMock)).toContain('POST /jobs');
    const body = fetchMock.mock.calls.find(([, init]) => init?.method === 'POST')?.[1]?.body;
    expect(JSON.parse(String(body))).toEqual({ kind: 'llm.music_caption', params: { description: 'piano' } });
    act(() => result.current.reset());
    expect(result.current.jobId).toBeNull();
  });

  it('WHEN el trabajo falla THEN devuelve su código de error', async () => {
    const { result } = task(
      api({ 'POST /jobs': { id: 6 }, '/jobs': [{ id: 6, kind: 'llm.music_caption', status: 'error', error_code: 'llm_timeout' }] }),
    );

    act(() => result.current.run({}));

    await waitFor(() => expect(result.current.error).toBe('llm_timeout'));
  });

  it('WHEN el trabajo sigue en curso THEN está ocupado', async () => {
    const { result } = task(api({ 'POST /jobs': { id: 7 }, '/jobs': [{ id: 7, kind: 'llm.music_caption', status: 'running' }] }));

    act(() => result.current.run({}));

    await waitFor(() => expect(result.current.jobId).toBe(7));
    expect(result.current.busy).toBe(true);
  });

  it('WHEN no se pudo encolar THEN el error es process_failed', async () => {
    const fetchMock = vi.fn(async () => new Response(JSON.stringify({ code: 'invalid_text' }), { status: 422 }));
    const { result } = task(fetchMock as never);

    act(() => result.current.run({}));

    await waitFor(() => expect(result.current.error).toBe('process_failed'));
  });

  it('assistantReady exige el runtime y el modelo elegido instalados', () => {
    expect(assistantReady(STATUS)).toBe(true);
    expect(assistantReady({ ...STATUS, runtime_installed: false })).toBe(false);
    expect(assistantReady({ ...STATUS, selected: 'qwen3.5-9b' })).toBe(false);
    expect(assistantReady(undefined)).toBe(false);
  });
});

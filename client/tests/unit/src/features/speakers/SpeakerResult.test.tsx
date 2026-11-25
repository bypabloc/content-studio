import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { SpeakerResult } from '@/features/speakers/SpeakerResult'
import { t } from '@/shared/i18n/t'

const { api } = vi.hoisted(() => ({
  api: { get: vi.fn(), post: vi.fn(), put: vi.fn(), fileUrl: (path: string) => `file://${path}` },
}))
vi.mock('@/shared/api/context', () => ({ useApi: () => api }))
vi.mock('@tauri-apps/plugin-opener', () => ({ openPath: vi.fn() }))
vi.mock('@/shared/media/useSyncedMedia', () => ({
  useSyncedMedia: () => ({ time: 0, playing: false, seek: vi.fn(), toggle: vi.fn() }),
}))
// La onda se simula (jsdom no la dibuja): la prueba mira la sección, no el dibujo.
vi.mock('wavesurfer.js', () => ({
  default: { create: vi.fn(() => ({ destroy: vi.fn(), on: vi.fn() })) },
}))
vi.mock('wavesurfer.js/dist/plugins/regions.js', () => ({
  default: { create: vi.fn(() => ({ on: vi.fn(), addRegion: vi.fn(), clearRegions: vi.fn() })) },
}))
vi.mock('wavesurfer.js/dist/plugins/timeline.js', () => ({ default: { create: vi.fn(() => ({})) } }))
vi.mock('wavesurfer.js/dist/plugins/zoom.js', () => ({ default: { create: vi.fn(() => ({})) } }))

const DIARIZATION = {
  source: 'C:/in/charla.wav',
  duration: 4,
  turns: [{ start: 0, end: 1, speaker: 'SPEAKER_00' }],
  exclusive_turns: [
    { start: 0, end: 1, speaker: 'SPEAKER_00' },
    { start: 1, end: 3, speaker: 'SPEAKER_01' },
  ],
  speakers: {
    SPEAKER_00: { name: 'Hablante 1', color: '#2563eb' },
    SPEAKER_01: { name: 'Hablante 2', color: '#dc2626' },
  },
  files: { json: 'D:/out/diarize-job/turns.json', rttm: 'D:/out/diarize-job/turns.rttm', csv: 'D:/out/diarize-job/turns.csv' },
  split: null,
}

let job: Record<string, unknown> = {}
let diarization: Record<string, unknown> = {}

beforeEach(() => {
  job = { id: 7, kind: 'diarize', status: 'done', progress: 1, params: { input: 'C:/in/charla.wav' } }
  diarization = { ...DIARIZATION }
  api.get.mockImplementation(async (path: string) => {
    if (path === '/jobs/7') return job
    if (path === '/diarizations/7') return diarization
    return null
  })
  api.put.mockImplementation(async (_path: string, body: unknown) => body)
  api.post.mockResolvedValue({ id: 8 })
})

afterEach(() => {
  cleanup()
  vi.clearAllMocks()
})

function renderResult() {
  render(
    <QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>
      <SpeakerResult jobId={7} />
    </QueryClientProvider>,
  )
}

describe('SpeakerResult [AC-2, AC-3, AC-4]', () => {
  it.each(['error', 'cancelled'])('WHEN the job ended with %s THEN it says the identification did not finish', async (status) => {
    job = { ...job, status }
    renderResult()

    expect(await screen.findByText(t('speakers.result.failed'))).toBeTruthy()
  })

  it('WHEN the diarization has no speech THEN it says so', async () => {
    diarization = { ...DIARIZATION, exclusive_turns: [] }
    renderResult()

    expect(await screen.findByText(t('speakers.empty'))).toBeTruthy()
  })

  it('WHEN the source is a video THEN the player is a video', async () => {
    diarization = { ...DIARIZATION, source: 'C:/in/charla.mp4' }
    renderResult()

    await waitFor(() => expect(document.querySelector('video')).not.toBeNull())
  })

  it('WHEN a speaker is picked in Only this speaker THEN it shows as the focus, and All clears it', async () => {
    renderResult()

    await userEvent.click(await screen.findByRole('combobox', { name: t('speakers.focus') }))
    await userEvent.click(await screen.findByRole('option', { name: 'Hablante 2' }))
    expect((screen.getByRole('combobox', { name: t('speakers.focus') }) as HTMLInputElement).value).toBe('Hablante 2')

    await userEvent.click(screen.getByRole('combobox', { name: t('speakers.focus') }))
    await userEvent.click(await screen.findByRole('option', { name: t('speakers.focus.all') }))
    expect((screen.getByRole('combobox', { name: t('speakers.focus') }) as HTMLInputElement).value).toBe(t('speakers.focus.all'))
  })

  it('WHEN a rename cannot be saved THEN the name goes back to the saved one', async () => {
    api.put.mockRejectedValue(new Error('down'))
    renderResult()
    const field = await screen.findByDisplayValue('Hablante 1')

    fireEvent.change(field, { target: { value: 'Ana' } })
    fireEvent.keyDown(field, { key: 'Enter' })

    await waitFor(() => expect(api.put).toHaveBeenCalled())
    await waitFor(() => expect(screen.getByDisplayValue('Hablante 1')).toBeTruthy())
  })

  it('WHEN one audio per speaker is asked THEN the page says it is splitting', async () => {
    renderResult()

    await userEvent.click(await screen.findByRole('button', { name: t('speakers.split') }))

    expect(await screen.findByText(t('speakers.split.running'))).toBeTruthy()
  })
})

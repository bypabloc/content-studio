import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { SpeakersPage } from '@/features/speakers/SpeakersPage'
import { t } from '@/shared/i18n/t'

const { api } = vi.hoisted(() => ({
  api: { get: vi.fn(), post: vi.fn(), put: vi.fn(), fileUrl: (path: string) => `file://${path}` },
}))
vi.mock('@/shared/api/context', () => ({ useApi: () => api }))
vi.mock('@tauri-apps/plugin-dialog', () => ({ open: vi.fn() }))
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

const SPEAKERS = {
  SPEAKER_00: { name: 'Hablante 1', color: '#2563eb' },
  SPEAKER_01: { name: 'Hablante 2', color: '#dc2626' },
}
const DIARIZATION = {
  source: 'C:/in/charla.wav',
  duration: 4,
  turns: [{ start: 0, end: 1, speaker: 'SPEAKER_00' }],
  exclusive_turns: [
    { start: 0, end: 1, speaker: 'SPEAKER_00' },
    { start: 1, end: 3, speaker: 'SPEAKER_01' },
  ],
  speakers: SPEAKERS,
  files: { json: 'D:/out/diarize-job/turns.json', rttm: 'D:/out/diarize-job/turns.rttm', csv: 'D:/out/diarize-job/turns.csv' },
  split: null,
}

let job7: Record<string, unknown> = {}

beforeEach(() => {
  job7 = { id: 7, kind: 'diarize', status: 'done', progress: 1, params: { input: 'C:/in/charla.wav' } }
  api.get.mockImplementation(async (path: string) => {
    if (path === '/engines') return []
    if (path.startsWith('/settings/')) return { key: path.slice('/settings/'.length), value: null }
    if (path === '/jobs/7') return job7
    if (path === '/diarizations/7') return DIARIZATION
    return null
  })
  api.put.mockImplementation(async (_path: string, body: unknown) => body)
  window.location.hash = ''
})

afterEach(() => {
  cleanup()
  vi.clearAllMocks()
})

function renderPage() {
  render(
    <QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>
      <SpeakersPage />
    </QueryClientProvider>,
  )
}

describe('SpeakersPage [AC-1, AC-3, AC-7]', () => {
  it('WHEN the section opens with from_job of a finished diarization THEN it shows its timeline without queueing a job', async () => {
    window.location.hash = '#/speakers?from_job=7'
    renderPage()

    expect(await screen.findByRole('group', { name: t('speakers.timeline.label') })).toBeTruthy()
    expect(api.post).not.toHaveBeenCalled()
  })

  it('WHEN a speaker is renamed THEN the whole map is saved with the new name', async () => {
    window.location.hash = '#/speakers?from_job=7'
    renderPage()
    const field = await screen.findByRole('textbox', { name: t('speakers.legend.rename', { name: 'Hablante 1' }) })

    fireEvent.change(field, { target: { value: 'Ana' } })
    fireEvent.keyDown(field, { key: 'Enter' })

    await waitFor(() =>
      expect(api.put).toHaveBeenCalledWith('/jobs/7/speakers', {
        SPEAKER_00: { name: 'Ana', color: '#2563eb' },
        SPEAKER_01: { name: 'Hablante 2', color: '#dc2626' },
      }),
    )
  })

  it('WHEN the job is still running THEN it shows its progress', async () => {
    job7 = { id: 7, kind: 'diarize', status: 'running', progress: 0.4, params: { input: 'C:/in/charla.wav' } }
    window.location.hash = '#/speakers?from_job=7'
    renderPage()

    expect(await screen.findByRole('progressbar', { name: t('speakers.progress') })).toBeTruthy()
  })
})

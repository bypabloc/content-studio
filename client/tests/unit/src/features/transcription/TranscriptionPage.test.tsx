import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { cleanup, render, screen } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { TranscriptionPage } from '@/features/transcription/TranscriptionPage'
import { t } from '@/shared/i18n/t'

const { api } = vi.hoisted(() => ({
  api: { get: vi.fn(), post: vi.fn(), put: vi.fn(), fileUrl: (path: string) => `file://${path}` },
}))
vi.mock('@/shared/api/context', () => ({ useApi: () => api }))
vi.mock('@tauri-apps/plugin-dialog', () => ({ open: vi.fn() }))
vi.mock('@tauri-apps/plugin-opener', () => ({ openPath: vi.fn() }))
vi.mock('@/shared/components/molecules/UIWhisperModelSelect', () => ({ UIWhisperModelSelect: () => null }))
vi.mock('@/shared/media/useSyncedMedia', () => ({
  useSyncedMedia: () => ({ time: 0, playing: false, seek: vi.fn(), toggle: vi.fn() }),
}))

const ENGINES = [
  {
    engine: 'faster-whisper',
    family: 'transcription',
    status: 'installed',
    models: [{ model: 'large-v3-turbo', size_gb: 1.6, downloaded: true, recommended: true }],
  },
  { engine: 'pyannote', family: 'diarization', status: 'missing', models: [] },
]
const TRANSCRIPT = {
  source: 'charla.wav',
  duration: 1,
  speakers: {},
  segments: [{ start: 0, end: 1, text: 'hola', speaker: null, words: [] }],
}

let job3: Record<string, unknown> = {}

function job(status: string, progress = 0) {
  return { id: 3, kind: 'transcribe', status, progress, params: { input: 'charla.wav' } }
}

beforeEach(() => {
  job3 = job('running', 0.4)
  api.get.mockImplementation(async (path: string) => {
    if (path === '/engines') return ENGINES
    if (path.startsWith('/settings/')) return { key: path.slice('/settings/'.length), value: null }
    if (path === '/jobs/3') return job3
    if (path === '/jobs/3/transcript') return TRANSCRIPT
    return null
  })
  window.location.hash = ''
})

afterEach(() => {
  cleanup()
  vi.clearAllMocks()
})

function renderPage() {
  render(
    <QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>
      <TranscriptionPage />
    </QueryClientProvider>,
  )
}

describe('TranscriptionPage [AC-1, D-1, D-5]', () => {
  it('WHEN the section opens without a job THEN it shows the title and the form, without progress', async () => {
    renderPage()

    expect(await screen.findByText(t('transcription.title'))).toBeTruthy()
    expect(screen.queryByRole('progressbar')).toBeNull()
  })

  it('WHEN a running job is opened with from_job THEN it shows its progress', async () => {
    window.location.hash = '#/transcription?from_job=3'
    renderPage()

    expect(await screen.findByRole('progressbar', { name: t('transcription.progress') })).toBeTruthy()
  })

  it('WHEN the job is done THEN it shows its transcript', async () => {
    job3 = job('done')
    window.location.hash = '#/transcription?from_job=3'
    renderPage()

    expect(await screen.findByText('hola')).toBeTruthy()
  })

  it('WHEN the job failed THEN it says so', async () => {
    job3 = job('error')
    window.location.hash = '#/transcription?from_job=3'
    renderPage()

    expect(await screen.findByText(t('transcription.job_failed'))).toBeTruthy()
  })
})

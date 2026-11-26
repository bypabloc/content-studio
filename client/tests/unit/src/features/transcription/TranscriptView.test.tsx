import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { TranscriptView } from '@/features/transcription/TranscriptView'
import { t } from '@/shared/i18n/t'

const { api, openPath, seek } = vi.hoisted(() => ({
  api: { get: vi.fn(), post: vi.fn(), put: vi.fn(), fileUrl: (path: string) => `file://${path}` },
  openPath: vi.fn(),
  seek: vi.fn(),
}))
vi.mock('@/shared/api/context', () => ({ useApi: () => api }))
vi.mock('@tauri-apps/plugin-opener', () => ({ openPath }))
vi.mock('@/shared/media/useSyncedMedia', () => ({
  useSyncedMedia: () => ({ time: 0, playing: false, seek, toggle: vi.fn() }),
}))

const SPEAKERS = {
  SPEAKER_00: { name: 'Ana', color: '#2563eb' },
  SPEAKER_01: { name: 'Luis', color: '#dc2626' },
}
const TRANSCRIPT = {
  source: 'charla.wav',
  duration: 3,
  speakers: SPEAKERS,
  segments: [
    {
      start: 0,
      end: 1,
      text: 'hola amigo',
      speaker: 'SPEAKER_00',
      words: [
        { start: 0, end: 0.5, word: ' hola', probability: 0.9, speaker: 'SPEAKER_00' },
        { start: 0.6, end: 1, word: ' amigo', probability: 0.9, speaker: 'SPEAKER_00' },
      ],
    },
    {
      start: 2.5,
      end: 3,
      text: 'mundo',
      speaker: 'SPEAKER_01',
      words: [{ start: 2.5, end: 3, word: ' mundo', probability: 0.9, speaker: 'SPEAKER_01' }],
    },
  ],
}

function renderView() {
  render(
    <QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>
      <TranscriptView jobId={1} />
    </QueryClientProvider>,
  )
}

beforeEach(() => {
  api.get.mockResolvedValue(TRANSCRIPT)
  api.put.mockImplementation(async (_path: string, body: unknown) => body)
  api.post.mockResolvedValue({ id: 7, path: 'D:/out/transcript.txt' })
  window.location.hash = ''
})

afterEach(() => {
  cleanup()
  vi.clearAllMocks()
})

describe('TranscriptView [AC-4, AC-5, AC-6, AC-7]', () => {
  it('WHEN the job has speakers THEN each block shows its name and its words', async () => {
    renderView()

    expect(await screen.findByText('Ana')).toBeTruthy()
    expect(screen.getByRole('button', { name: 'hola' })).toBeTruthy()
    expect(screen.getByRole('button', { name: 'mundo' })).toBeTruthy()
  })

  it('WHEN a word is clicked THEN the player goes to its start', async () => {
    renderView()

    fireEvent.click(await screen.findByRole('button', { name: 'mundo' }))

    expect(seek).toHaveBeenCalledWith(2.5)
  })

  it('WHEN the job has no speakers THEN it shows one paragraph per segment without names', async () => {
    api.get.mockResolvedValue({
      ...TRANSCRIPT,
      speakers: {},
      segments: [{ start: 0, end: 1, text: 'hola amigo', words: [] }],
    })
    renderView()

    expect(await screen.findByText('hola amigo')).toBeTruthy()
    expect(screen.queryByText('Ana')).toBeNull()
  })

  it('WHEN there are no words THEN it says that no voice was detected', async () => {
    api.get.mockResolvedValue({ ...TRANSCRIPT, segments: [] })
    renderView()

    expect(await screen.findByText(t('transcription.empty'))).toBeTruthy()
  })

  it('WHEN a speaker is renamed THEN the whole map is saved', async () => {
    renderView()
    const field = await screen.findByRole('textbox', { name: t('speakers.legend.rename', { name: 'Ana' }) })

    fireEvent.change(field, { target: { value: 'Elena' } })
    fireEvent.blur(field)

    await waitFor(() =>
      expect(api.put).toHaveBeenCalledWith('/jobs/1/speakers', {
        SPEAKER_00: { name: 'Elena', color: '#2563eb' },
        SPEAKER_01: { name: 'Luis', color: '#dc2626' },
      }),
    )
  })

  it('WHEN the text is exported with timestamps THEN it posts the export and shows where the file is', async () => {
    renderView()
    await userEvent.click(await screen.findByRole('switch', { name: t('transcription.export.timestamps') }))

    await userEvent.click(screen.getByRole('button', { name: t('transcription.export.txt') }))

    await waitFor(() => expect(api.post).toHaveBeenCalledWith('/jobs/1/transcript/export', { timestamps: true }))
    expect(await screen.findByText(t('transcription.exported', { path: 'D:/out/transcript.txt' }))).toBeTruthy()
  })

  it('WHEN subtitles are created THEN it posts from-transcript and opens that project', async () => {
    renderView()

    await userEvent.click(await screen.findByRole('button', { name: t('transcription.to_subtitles') }))

    await waitFor(() => expect(api.post).toHaveBeenCalledWith('/subtitles/from-transcript', { job_id: 1 }))
    await waitFor(() => expect(window.location.hash).toContain('/subtitles?project=7'))
  })
})

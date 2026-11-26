import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { cleanup, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { SpeakerFiles } from '@/features/speakers/SpeakerFiles'
import { t } from '@/shared/i18n/t'

const { api, openPath } = vi.hoisted(() => ({
  api: { get: vi.fn(), post: vi.fn(), put: vi.fn(), fileUrl: (path: string) => `file://${path}` },
  openPath: vi.fn(),
}))
vi.mock('@/shared/api/context', () => ({ useApi: () => api }))
vi.mock('@tauri-apps/plugin-opener', () => ({ openPath }))

const SOURCE = 'C:/in/charla.wav'
const FILES = {
  json: 'D:/out/diarize-job/turns.json',
  rttm: 'D:/out/diarize-job/turns.rttm',
  csv: 'D:/out/diarize-job/turns.csv',
}
const SPEAKERS = {
  SPEAKER_00: { name: 'Ana', color: '#2563eb' },
  SPEAKER_01: { name: 'Luis', color: '#dc2626' },
}

function renderWithClient(ui: React.ReactElement) {
  return render(<QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>{ui}</QueryClientProvider>)
}

beforeEach(() => {
  api.post.mockResolvedValue({ id: 8 })
})

afterEach(() => {
  cleanup()
  vi.clearAllMocks()
})

describe('SpeakerFiles [AC-4, AC-5, AC-6]', () => {
  it('WHEN the result has its files THEN it lists them and Open folder opens the job folder', async () => {
    renderWithClient(<SpeakerFiles jobId={7} source={SOURCE} files={FILES} split={null} speakers={SPEAKERS} />)

    expect(screen.getByText('turns.csv')).toBeTruthy()
    await userEvent.click(screen.getByRole('button', { name: t('speakers.files.open_folder') }))

    expect(openPath).toHaveBeenCalledWith('D:/out/diarize-job')
  })

  it('WHEN one audio per speaker is asked THEN it queues diarize.split with the input and the turns folder', async () => {
    const onSplitQueued = vi.fn()
    renderWithClient(<SpeakerFiles jobId={7} source={SOURCE} files={FILES} split={null} speakers={SPEAKERS} onSplitQueued={onSplitQueued} />)

    await userEvent.click(screen.getByRole('button', { name: t('speakers.split') }))

    await waitFor(() =>
      expect(api.post).toHaveBeenCalledWith('/jobs', { kind: 'diarize.split', params: { input: SOURCE, turns: 'D:/out/diarize-job' } }),
    )
    await waitFor(() => expect(onSplitQueued).toHaveBeenCalledWith(8))
  })

  it('WHEN the split is ready THEN each speaker has its own player, named', () => {
    const split = { SPEAKER_00: 'D:/out/split/speakers/SPEAKER_00.wav', SPEAKER_01: 'D:/out/split/speakers/SPEAKER_01.wav' }
    renderWithClient(<SpeakerFiles jobId={7} source={SOURCE} files={FILES} split={split} speakers={SPEAKERS} />)

    expect(document.querySelectorAll('audio')).toHaveLength(2)
    expect(screen.getByLabelText('Ana')).toBeTruthy()
    expect(screen.getByLabelText('Luis')).toBeTruthy()
  })

  it('WHEN Open in the Editor is pressed THEN it creates the project from the job and navigates to it', async () => {
    api.post.mockResolvedValue({ project: 'D:/out/editor/2026-11-25-charla/project.json' })
    renderWithClient(<SpeakerFiles jobId={7} source={SOURCE} files={FILES} split={null} speakers={SPEAKERS} />)

    await userEvent.click(screen.getByRole('button', { name: t('speakers.to_editor') }))

    await waitFor(() => expect(api.post).toHaveBeenCalledWith('/editor/projects/from-diarization', { job: 7 }))
    await waitFor(() => expect(window.location.hash).toContain('/editor?project='))
  })

  it('WHEN there is only one speaker THEN there is nothing to split', () => {
    renderWithClient(<SpeakerFiles jobId={7} source={SOURCE} files={FILES} split={null} speakers={{ SPEAKER_00: SPEAKERS.SPEAKER_00 }} />)

    expect(screen.queryByRole('button', { name: t('speakers.split') })).toBeNull()
  })

  it('WHEN a split speaker is not in the legend THEN its id labels the player', () => {
    const split = { SPEAKER_09: 'D:/out/split/speakers/SPEAKER_09.wav' }
    renderWithClient(<SpeakerFiles jobId={7} source={SOURCE} files={FILES} split={split} speakers={SPEAKERS} />)

    expect(screen.getByLabelText('SPEAKER_09')).toBeTruthy()
  })

  it('WHEN the split is asked without a listener THEN it still queues the job', async () => {
    renderWithClient(<SpeakerFiles jobId={7} source={SOURCE} files={FILES} split={null} speakers={SPEAKERS} />)

    await userEvent.click(screen.getByRole('button', { name: t('speakers.split') }))

    await waitFor(() => expect(api.post).toHaveBeenCalledWith('/jobs', { kind: 'diarize.split', params: { input: SOURCE, turns: 'D:/out/diarize-job' } }))
  })
})

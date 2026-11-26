import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { TranscriptionForm } from '@/features/transcription/TranscriptionForm'
import { t } from '@/shared/i18n/t'

const { api, open } = vi.hoisted(() => ({
  api: { get: vi.fn(), post: vi.fn(), put: vi.fn(), fileUrl: (path: string) => `file://${path}` },
  open: vi.fn(),
}))
vi.mock('@/shared/api/context', () => ({ useApi: () => api }))
vi.mock('@tauri-apps/plugin-dialog', () => ({ open }))
vi.mock('@/shared/components/molecules/UIWhisperModelSelect', () => ({ UIWhisperModelSelect: () => null }))

function engines(pyannoteStatus: string) {
  return [
    {
      engine: 'faster-whisper',
      family: 'transcription',
      status: 'installed',
      models: [{ model: 'large-v3-turbo', size_gb: 1.6, downloaded: true, recommended: true }],
    },
    { engine: 'pyannote', family: 'diarization', status: pyannoteStatus, models: [] },
  ]
}

function renderForm(onQueued = vi.fn()) {
  render(
    <QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>
      <TranscriptionForm onQueued={onQueued} />
    </QueryClientProvider>,
  )
  return onQueued
}

beforeEach(() => {
  api.get.mockImplementation(async (path: string) => {
    if (path === '/engines') return engines('installed')
    if (path.startsWith('/settings/')) return { key: path.slice('/settings/'.length), value: null }
    return null
  })
  api.post.mockResolvedValue({ id: 9 })
})

afterEach(() => {
  cleanup()
  vi.clearAllMocks()
})

describe('TranscriptionForm [AC-2, AC-3]', () => {
  it('WHEN pyannote is not installed THEN the speaker switch is disabled and points to Engines', async () => {
    api.get.mockImplementation(async (path: string) => (path === '/engines' ? engines('missing') : { key: path, value: null }))
    renderForm()

    const speakers = await screen.findByRole('switch', { name: t('transcription.diarize') })

    expect(speakers.matches('[disabled], [aria-disabled="true"], [data-disabled]')).toBe(true)
    expect(screen.getByText(t('transcription.diarize.missing'))).toBeTruthy()
    expect(screen.getByRole('link', { name: t('transcription.diarize.engines') }).getAttribute('href')).toBe('#/engines')
  })

  it('WHEN speakers are identified with exactly 2 THEN it queues transcribe with the count and reports the job', async () => {
    const onQueued = renderForm()
    fireEvent.change(await screen.findByLabelText(t('transcription.file')), { target: { value: 'charla.wav' } })
    await userEvent.click(await screen.findByRole('switch', { name: t('transcription.diarize') }))
    await userEvent.click(await screen.findByRole('combobox', { name: t('speakers.count.label') }))
    await userEvent.click(await screen.findByRole('option', { name: t('speakers.count.exact') }))
    fireEvent.change(screen.getByRole('spinbutton', { name: t('speakers.count.number') }), { target: { value: '2' } })

    fireEvent.click(screen.getByRole('button', { name: t('transcription.start') }))

    await waitFor(() =>
      expect(api.post).toHaveBeenCalledWith('/jobs', {
        kind: 'transcribe',
        params: { input: 'charla.wav', model: 'large-v3-turbo', language: 'auto', diarize: true, num_speakers: 2 },
      }),
    )
    await waitFor(() => expect(onQueued).toHaveBeenCalledWith(9))
  })

  it('WHEN speakers are off THEN it queues a plain transcription without the speaker keys', async () => {
    renderForm()
    fireEvent.change(await screen.findByLabelText(t('transcription.file')), { target: { value: 'charla.wav' } })

    fireEvent.click(screen.getByRole('button', { name: t('transcription.start') }))

    await waitFor(() =>
      expect(api.post).toHaveBeenCalledWith('/jobs', {
        kind: 'transcribe',
        params: { input: 'charla.wav', model: 'large-v3-turbo', language: 'auto' },
      }),
    )
  })

  it('WHEN the file is chosen with the system dialog THEN its path fills the field', async () => {
    open.mockResolvedValue('D:/media/charla.wav')
    renderForm()

    fireEvent.click(await screen.findByRole('button', { name: t('transcription.choose') }))

    await waitFor(() =>
      expect((screen.getByLabelText(t('transcription.file')) as HTMLInputElement).value).toBe('D:/media/charla.wav'),
    )
  })
})

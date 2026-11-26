import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { SpeakersForm } from '@/features/speakers/SpeakersForm'
import { t } from '@/shared/i18n/t'

const { api, open } = vi.hoisted(() => ({
  api: { get: vi.fn(), post: vi.fn(), put: vi.fn(), fileUrl: (path: string) => `file://${path}` },
  open: vi.fn(),
}))
vi.mock('@/shared/api/context', () => ({ useApi: () => api }))
vi.mock('@tauri-apps/plugin-dialog', () => ({ open }))

function renderForm(onQueued = vi.fn()) {
  render(
    <QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>
      <SpeakersForm onQueued={onQueued} />
    </QueryClientProvider>,
  )
  return onQueued
}

beforeEach(() => {
  api.get.mockImplementation(async (path: string) => {
    if (path.startsWith('/settings/')) return { key: path.slice('/settings/'.length), value: null }
    return null
  })
  api.post.mockResolvedValue({ id: 9 })
})

afterEach(() => {
  cleanup()
  vi.clearAllMocks()
})

describe('SpeakersForm [AC-1]', () => {
  it('WHEN a file is chosen in automatic mode and Identify is pressed THEN it queues diarize with only the input', async () => {
    const onQueued = renderForm()

    fireEvent.change(screen.getByRole('textbox', { name: t('transcription.file') }), { target: { value: 'charla.wav' } })
    await userEvent.click(screen.getByRole('button', { name: t('speakers.start') }))

    await waitFor(() => expect(api.post).toHaveBeenCalledWith('/jobs', { kind: 'diarize', params: { input: 'charla.wav' } }))
    await waitFor(() => expect(onQueued).toHaveBeenCalledWith(9))
  })

  it('WHEN exactly 2 speakers are chosen THEN it queues diarize with num_speakers 2', async () => {
    renderForm()

    fireEvent.change(screen.getByRole('textbox', { name: t('transcription.file') }), { target: { value: 'charla.wav' } })
    await userEvent.click(await screen.findByRole('combobox', { name: t('speakers.count.label') }))
    await userEvent.click(await screen.findByRole('option', { name: t('speakers.count.exact') }))
    fireEvent.change(screen.getByRole('spinbutton', { name: t('speakers.count.number') }), { target: { value: '2' } })
    await userEvent.click(screen.getByRole('button', { name: t('speakers.start') }))

    await waitFor(() =>
      expect(api.post).toHaveBeenCalledWith('/jobs', { kind: 'diarize', params: { input: 'charla.wav', num_speakers: 2 } }),
    )
  })

  it('WHEN no file is chosen THEN Identify is disabled', () => {
    renderForm()

    expect((screen.getByRole('button', { name: t('speakers.start') }) as HTMLButtonElement).disabled).toBe(true)
  })

  it('WHEN a file is picked in the dialog THEN its path fills the field', async () => {
    open.mockResolvedValue('C:/in/charla.wav')
    renderForm()

    await userEvent.click(screen.getByRole('button', { name: t('transcription.choose') }))

    expect((screen.getByRole('textbox', { name: t('transcription.file') }) as HTMLInputElement).value).toBe('C:/in/charla.wav')
  })

  it('WHEN the dialog is cancelled THEN the field stays empty', async () => {
    open.mockResolvedValue(null)
    renderForm()

    await userEvent.click(screen.getByRole('button', { name: t('transcription.choose') }))

    expect((screen.getByRole('textbox', { name: t('transcription.file') }) as HTMLInputElement).value).toBe('')
  })

  it('WHEN the job cannot be queued THEN the form says so', async () => {
    api.post.mockRejectedValue(new Error('down'))
    renderForm()
    fireEvent.change(screen.getByRole('textbox', { name: t('transcription.file') }), { target: { value: 'charla.wav' } })

    await userEvent.click(screen.getByRole('button', { name: t('speakers.start') }))

    expect(await screen.findByText(t('speakers.failed'))).toBeTruthy()
  })
})

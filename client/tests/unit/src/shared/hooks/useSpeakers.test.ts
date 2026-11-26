import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { act, renderHook, waitFor } from '@testing-library/react'
import { createElement, type ReactNode } from 'react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { useSaveSpeakers } from '@/shared/hooks/useSpeakers'

const { api } = vi.hoisted(() => ({ api: { put: vi.fn() } }))
vi.mock('@/shared/api/context', () => ({ useApi: () => api }))

const SPEAKERS = { SPEAKER_00: { name: 'Ana', color: '#2563eb' } }

afterEach(() => {
  vi.clearAllMocks()
})

describe('useSaveSpeakers [AC-5]', () => {
  it('WHEN the speakers are saved THEN it PUTs the whole map and reads the transcript and the speakers again', async () => {
    api.put.mockResolvedValue(SPEAKERS)
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    const invalidate = vi.spyOn(queryClient, 'invalidateQueries')
    const wrapper = ({ children }: { children: ReactNode }) => createElement(QueryClientProvider, { client: queryClient }, children)
    const { result } = renderHook(() => useSaveSpeakers(1), { wrapper })

    act(() => {
      result.current.mutate(SPEAKERS)
    })
    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(api.put).toHaveBeenCalledWith('/jobs/1/speakers', SPEAKERS)
    expect(invalidate).toHaveBeenCalledWith({ queryKey: ['transcript', 1] })
    expect(invalidate).toHaveBeenCalledWith({ queryKey: ['speakers', 1] })
  })
})

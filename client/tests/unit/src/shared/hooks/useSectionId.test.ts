import { renderHook, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it } from 'vitest'

import { useSectionId } from '@/shared/hooks/useSectionId'

describe('useSectionId', () => {
  afterEach(() => {
    window.location.hash = ''
  })

  it('WHEN the hash is #/settings THEN the section is settings', () => {
    window.location.hash = '#/settings'

    const { result } = renderHook(() => useSectionId())

    expect(result.current).toBe('settings')
  })

  it('WHEN the hash changes THEN the section follows without a reload', async () => {
    const { result } = renderHook(() => useSectionId())

    window.location.hash = '#/narration'

    await waitFor(() => expect(result.current).toBe('narration'))
  })
})

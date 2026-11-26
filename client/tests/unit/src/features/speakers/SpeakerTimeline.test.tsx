import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import WaveSurfer from 'wavesurfer.js'

import { SpeakerTimeline } from '@/features/speakers/SpeakerTimeline'
import { t } from '@/shared/i18n/t'

// La onda y sus plugins se simulan: jsdom no dibuja la forma de onda. Se prueban las regiones, el clic y el teclado.
const { regions, instance } = vi.hoisted(() => {
  const listeners: Record<string, Array<(...args: unknown[]) => void>> = {}
  const waveListeners: Record<string, Array<(...args: unknown[]) => void>> = {}
  return {
    regions: {
      listeners,
      addRegion: vi.fn((options: { id: string; start: number; end: number }) => ({ ...options })),
      clearRegions: vi.fn(),
      on: vi.fn((event: string, handler: (...args: unknown[]) => void) => {
        ;(listeners[event] ??= []).push(handler)
        return () => undefined
      }),
    },
    instance: {
      destroy: vi.fn(),
      waveListeners,
      on: vi.fn((event: string, handler: (...args: unknown[]) => void) => {
        ;(waveListeners[event] ??= []).push(handler)
        return () => undefined
      }),
    },
  }
})

vi.mock('wavesurfer.js', () => ({ default: { create: vi.fn(() => instance) } }))
vi.mock('wavesurfer.js/dist/plugins/regions.js', () => ({ default: { create: vi.fn(() => regions) } }))
vi.mock('wavesurfer.js/dist/plugins/timeline.js', () => ({ default: { create: vi.fn(() => ({})) } }))
vi.mock('wavesurfer.js/dist/plugins/zoom.js', () => ({ default: { create: vi.fn(() => ({})) } }))

function fire(event: string, region: { id: string }) {
  for (const handler of regions.listeners[event] ?? []) handler(region)
}

// WaveSurfer avisa «ready» cuando el audio ya tiene duración: solo entonces se dibujan las regiones.
function fireReady() {
  for (const handler of instance.waveListeners.ready ?? []) handler(6)
}

const SPEAKERS = {
  SPEAKER_00: { name: 'Ana', color: '#2563eb' },
  SPEAKER_01: { name: 'Luis', color: '#dc2626' },
}
const TURNS = [
  { start: 0, end: 1, speaker: 'SPEAKER_00' },
  { start: 1, end: 3, speaker: 'SPEAKER_01' },
  { start: 4, end: 5, speaker: 'SPEAKER_00' },
]

function renderTimeline(props: Partial<Parameters<typeof SpeakerTimeline>[0]> = {}) {
  const onSeek = vi.fn()
  const base = { media: null, peaks: [], duration: 6, turns: TURNS, speakers: SPEAKERS, time: 0, focusSpeaker: null, onSeek }
  const view = render(<SpeakerTimeline {...base} {...props} />)
  return { onSeek, rerender: (next: Partial<Parameters<typeof SpeakerTimeline>[0]>) => view.rerender(<SpeakerTimeline {...base} {...props} {...next} />) }
}

function regionOptions(id: string): Record<string, unknown> {
  const found = regions.addRegion.mock.calls.map(([options]) => options).filter((options) => options.id === id).pop()
  return found ?? {}
}

beforeEach(() => {
  for (const key of Object.keys(regions.listeners)) delete regions.listeners[key]
  for (const key of Object.keys(instance.waveListeners)) delete instance.waveListeners[key]
  vi.clearAllMocks()
})

afterEach(() => {
  cleanup()
})

describe('SpeakerTimeline [AC-2, AC-3]', () => {
  it('WHEN the wave is ready THEN it draws one region per turn with the speaker color and name', () => {
    renderTimeline()

    expect(WaveSurfer.create).toHaveBeenCalledWith(expect.objectContaining({ duration: 6 }))
    expect(regions.addRegion).not.toHaveBeenCalled()

    fireReady()

    expect(regions.addRegion).toHaveBeenCalledTimes(3)
    expect(regionOptions('0')).toMatchObject({ start: 0, end: 1, content: 'Ana', drag: false, resize: false })
    expect(regionOptions('1')).toMatchObject({ start: 1, end: 3, content: 'Luis' })
    expect(regionOptions('0').color).toBe('rgba(37, 99, 235, 0.35)')
  })

  it('WHEN a region is clicked THEN the player goes to the start of its turn', () => {
    const { onSeek } = renderTimeline()
    fireReady()

    fire('region-clicked', { id: '1' })

    expect(onSeek).toHaveBeenCalledWith(1)
  })

  it('WHEN one speaker is focused THEN the regions of the other speaker are faded', () => {
    renderTimeline({ focusSpeaker: 'SPEAKER_00' })
    fireReady()

    expect(regionOptions('0').color).toBe('rgba(37, 99, 235, 0.35)')
    expect(regionOptions('1').color).toBe('rgba(220, 38, 38, 0.08)')
  })

  it('WHEN the right arrow is pressed with a speaker focused THEN the player goes to the next turn of that speaker', () => {
    const { onSeek } = renderTimeline({ focusSpeaker: 'SPEAKER_00', time: 1.5 })
    fireReady()

    fireEvent.keyDown(screen.getByRole('group', { name: t('speakers.timeline.label') }), { key: 'ArrowRight' })

    expect(onSeek).toHaveBeenCalledWith(4)
  })

  it('WHEN a speaker is renamed THEN the regions show the new name', () => {
    const { rerender } = renderTimeline()
    fireReady()

    rerender({ speakers: { ...SPEAKERS, SPEAKER_00: { name: 'Elena', color: '#2563eb' } } })

    expect(regionOptions('0').content).toBe('Elena')
  })

  it('WHEN the left arrow is pressed THEN the player goes to the previous turn', () => {
    const { onSeek } = renderTimeline({ time: 4.5 })
    fireReady()

    fireEvent.keyDown(screen.getByRole('group', { name: t('speakers.timeline.label') }), { key: 'ArrowLeft' })

    expect(onSeek).toHaveBeenCalledWith(4)
  })

  it('WHEN a turn has no speaker in the legend THEN its region shows the speaker id', () => {
    renderTimeline({ speakers: {} })
    fireReady()

    expect(regionOptions('0')).toMatchObject({ content: 'SPEAKER_00' })
  })
})

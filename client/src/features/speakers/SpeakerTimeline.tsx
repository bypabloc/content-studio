import { useEffect, useRef } from 'react'
import WaveSurfer from 'wavesurfer.js'
import RegionsPlugin from 'wavesurfer.js/dist/plugins/regions.js'
import TimelinePlugin from 'wavesurfer.js/dist/plugins/timeline.js'
import ZoomPlugin from 'wavesurfer.js/dist/plugins/zoom.js'

import { UIStack } from '@/shared/components/atoms/UIStack'
import type { SpeakerMap } from '@/shared/components/molecules/UISpeakerLegend'
import { t } from '@/shared/i18n/t'

/** Un turno exclusivo: en cada instante suena un solo hablante (spec 035, AC-3). */
export interface Turn {
  start: number
  end: number
  speaker: string
}

const FOCUS_ALPHA = 0.35
const DIM_ALPHA = 0.08
const FALLBACK_COLOR = '#64748b'
// Un tiempo a menos de esta distancia de un inicio cuenta como estar en él: las flechas no se quedan atascadas.
const EPSILON = 0.01

/** El color del hablante con su alfa: la región es translúcida para leer la onda debajo. */
function tint(hex: string, alpha: number): string {
  const value = Number.parseInt(hex.slice(1), 16)
  return `rgba(${(value >> 16) & 255}, ${(value >> 8) & 255}, ${value & 255}, ${alpha})`
}

// Reemplaza las regiones por las de los turnos: el hablante en foco se ve sólido y los demás, atenuados.
function drawTurns(
  plugin: ReturnType<typeof RegionsPlugin.create>,
  turns: Turn[],
  speakers: SpeakerMap,
  focusSpeaker: string | null,
): void {
  plugin.clearRegions()
  turns.forEach((turn, index) => {
    const speaker = speakers[turn.speaker]
    const focused = focusSpeaker === null || turn.speaker === focusSpeaker
    plugin.addRegion({
      id: String(index),
      start: turn.start,
      end: turn.end,
      color: tint(speaker?.color ?? FALLBACK_COLOR, focused ? FOCUS_ALPHA : DIM_ALPHA),
      content: speaker?.name ?? turn.speaker,
      drag: false,
      resize: false,
    })
  })
}

export interface SpeakerTimelineProps {
  media: HTMLMediaElement | null
  peaks: number[]
  duration: number
  turns: Turn[]
  speakers: SpeakerMap
  time: number
  focusSpeaker: string | null
  onSeek: (seconds: number) => void
}

/**
 * La línea de tiempo de la sección Hablantes (spec 037, AC-2 y AC-3): la onda con una región por turno, coloreada y con el
 * nombre de su hablante. Un clic en una región lleva el reproductor a su inicio; con un hablante en foco, las demás
 * regiones se atenúan y ← y → saltan entre sus turnos. Solo lectura: los bordes no se arrastran.
 */
export function SpeakerTimeline({
  media,
  peaks,
  duration,
  turns,
  speakers,
  time,
  focusSpeaker,
  onSeek,
}: SpeakerTimelineProps): React.JSX.Element {
  const container = useRef<HTMLDivElement>(null)
  const regions = useRef<ReturnType<typeof RegionsPlugin.create> | null>(null)
  const ready = useRef(false)
  // Los oyentes leen siempre los datos actuales, sin reengancharse en cada cambio.
  const latest = useRef({ turns, speakers, focusSpeaker, onSeek })

  useEffect(() => {
    latest.current = { turns, speakers, focusSpeaker, onSeek }
  })

  useEffect(() => {
    const plugin = RegionsPlugin.create()
    const instance = WaveSurfer.create({
      container: container.current as HTMLElement,
      media: media ?? undefined,
      peaks: [peaks],
      duration,
      height: 96,
      waveColor: 'oklch(0.705 0.015 286)',
      progressColor: 'oklch(0.541 0.281 293)',
      normalize: true,
      plugins: [plugin, TimelinePlugin.create(), ZoomPlugin.create()],
    })
    plugin.on('region-clicked', (region) => {
      const turn = latest.current.turns[Number(region.id)]
      if (turn) latest.current.onSeek(turn.start)
    })
    // Las regiones se dibujan al llegar «ready»: antes WaveSurfer no conoce la duración y fija cada región en 0.
    ready.current = false
    instance.on('ready', () => {
      ready.current = true
      drawTurns(plugin, latest.current.turns, latest.current.speakers, latest.current.focusSpeaker)
    })
    regions.current = plugin
    return () => {
      regions.current = null
      ready.current = false
      instance.destroy()
    }
  }, [media, peaks, duration])

  // Un nombre nuevo, un turno distinto o el foco cambian las regiones al instante (AC-3).
  useEffect(() => {
    if (regions.current && ready.current) drawTurns(regions.current, turns, speakers, focusSpeaker)
  }, [turns, speakers, focusSpeaker])

  function onKeyDown(event: React.KeyboardEvent): void {
    if (event.key !== 'ArrowRight' && event.key !== 'ArrowLeft') return
    const targets = turns
      .filter((turn) => focusSpeaker === null || turn.speaker === focusSpeaker)
      .sort((a, b) => a.start - b.start)
    const next =
      event.key === 'ArrowRight'
        ? targets.find((turn) => turn.start > time + EPSILON)
        : targets.filter((turn) => turn.start < time - EPSILON).pop()
    if (next) onSeek(next.start)
  }

  return (
    <UIStack
      ref={container}
      role="group"
      aria-label={t('speakers.timeline.label')}
      tabIndex={0}
      onKeyDown={onKeyDown}
      className="w-full"
    />
  )
}

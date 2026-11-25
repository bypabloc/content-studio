import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'

import { useApi } from '@/shared/api/context'
import type { components } from '@/shared/api/schema'
import { UIMedia } from '@/shared/components/atoms/UIMedia'
import { UIProgress } from '@/shared/components/atoms/UIProgress'
import { UISkeleton } from '@/shared/components/atoms/UISkeleton'
import { UIStack } from '@/shared/components/atoms/UIStack'
import { UIText } from '@/shared/components/atoms/UIText'
import { UISelect } from '@/shared/components/molecules/UISelect'
import { type SpeakerMap, UISpeakerLegend } from '@/shared/components/molecules/UISpeakerLegend'
import { t } from '@/shared/i18n/t'
import { useSyncedMedia } from '@/shared/media/useSyncedMedia'

import { type DiarizationFiles, SpeakerFiles } from './SpeakerFiles'
import { SpeakerTimeline, type Turn } from './SpeakerTimeline'

type Job = components['schemas']['Job']

/** El resultado de una identificación de hablantes (GET /diarizations/{id}, spec 037, AC-4). */
interface Diarization {
  source: string
  duration: number
  turns: Turn[]
  exclusive_turns: Turn[]
  speakers: SpeakerMap
  files: DiarizationFiles
  split: Record<string, string> | null
}

const FINISHED = ['done', 'error', 'cancelled']
const VIDEO = /\.(mp4|mov|mkv|webm|avi|m4v)$/i
const NO_PEAKS: number[] = []

/** El tipo de medio del reproductor: un video muestra su imagen; un audio, solo los controles. */
function kindOf(source: string): 'video' | 'audio' {
  return VIDEO.test(source) ? 'video' : 'audio'
}

/** Los segundos que habla cada hablante, para la leyenda. */
function secondsOf(turns: Turn[]): Record<string, number> {
  const totals: Record<string, number> = {}
  for (const turn of turns) totals[turn.speaker] = (totals[turn.speaker] ?? 0) + (turn.end - turn.start)
  return totals
}

/**
 * El resultado de un trabajo `diarize` (spec 037): su progreso mientras corre, y luego la sección con la línea de tiempo,
 * la leyenda, el foco por hablante y los archivos. Los nombres se guardan al instante (AC-3).
 */
export function SpeakerResult({ jobId }: { jobId: number }): React.JSX.Element {
  const api = useApi()
  const [splitting, setSplitting] = useState(false)
  const job = useQuery({
    queryKey: ['jobs', jobId],
    queryFn: () => api.get<Job>(`/jobs/${jobId}`),
    refetchInterval: (query) => (query.state.data && FINISHED.includes(query.state.data.status) ? false : 1000),
  })
  const done = job.data?.status === 'done'
  const result = useQuery({
    queryKey: ['diarization', jobId],
    queryFn: () => api.get<Diarization>(`/diarizations/${jobId}`),
    enabled: done,
    // Mientras se separan los audios, el resultado se vuelve a leer hasta que aparezcan.
    refetchInterval: (query) => (splitting && !query.state.data?.split ? 1000 : false),
  })

  if (!job.data) return <UISkeleton className="h-32 w-full rounded-xl" />
  if (job.data.status === 'error' || job.data.status === 'cancelled') {
    return <UIText variant="caption" className="text-destructive">{t('speakers.result.failed')}</UIText>
  }
  if (!done) return <UIProgress value={job.data.progress} label={t('speakers.progress')} />
  if (!result.data) return <UISkeleton className="h-64 w-full rounded-xl" />
  return (
    <DiarizationView
      jobId={jobId}
      data={result.data}
      splitting={splitting}
      onSplitQueued={() => setSplitting(true)}
    />
  )
}

function DiarizationView({
  jobId,
  data,
  splitting,
  onSplitQueued,
}: {
  jobId: number
  data: Diarization
  splitting: boolean
  onSplitQueued: () => void
}): React.JSX.Element {
  const api = useApi()
  const queryClient = useQueryClient()
  const key = ['diarization', jobId]
  const [media, setMedia] = useState<HTMLMediaElement | null>(null)
  const player = useSyncedMedia(media)
  const [focus, setFocus] = useState<string | null>(null)
  // Un guardado fallido vuelve a montar la leyenda: su borrador deja el nombre no guardado y toma el guardado.
  const [legendRev, setLegendRev] = useState(0)
  const peaks = useQuery({
    queryKey: ['peaks', data.source],
    queryFn: () => api.get<{ peaks: number[] }>(`/media/peaks?path=${encodeURIComponent(data.source)}&n=2000`),
  })

  // El nombre se muestra al instante: se guarda el mapa entero (AC-3) y, si falla, vuelve el anterior.
  const save = useMutation({
    mutationFn: (next: SpeakerMap) => api.put<SpeakerMap>(`/jobs/${jobId}/speakers`, next),
    onMutate: async (next) => {
      await queryClient.cancelQueries({ queryKey: key })
      const previous = queryClient.getQueryData<Diarization>(key)
      queryClient.setQueryData<Diarization>(key, (old) => (old ? { ...old, speakers: next } : old))
      return { previous }
    },
    onError: (_error, _next, context) => {
      if (context?.previous) queryClient.setQueryData(key, context.previous)
      setLegendRev((rev) => rev + 1)
    },
    onSettled: () => {
      void queryClient.invalidateQueries({ queryKey: key })
    },
  })

  if (data.exclusive_turns.length === 0) return <UIText variant="caption">{t('speakers.empty')}</UIText>
  const names = Object.keys(data.speakers)

  return (
    <UIStack gap="lg">
      <UIMedia kind={kindOf(data.source)} src={api.fileUrl(data.source)} controls className="w-full rounded-lg" mediaRef={setMedia} />
      <UISelect
        label={t('speakers.focus')}
        value={focus ?? ''}
        options={[
          { value: '', label: t('speakers.focus.all') },
          ...names.map((id) => ({ value: id, label: data.speakers[id]?.name ?? id })),
        ]}
        onChange={(value) => setFocus(value === '' ? null : value)}
      />
      <SpeakerTimeline
        media={media}
        peaks={peaks.data?.peaks ?? NO_PEAKS}
        duration={data.duration}
        turns={data.exclusive_turns}
        speakers={data.speakers}
        time={player.time}
        focusSpeaker={focus}
        onSeek={player.seek}
      />
      <UISpeakerLegend
        key={legendRev}
        speakers={data.speakers}
        durations={secondsOf(data.exclusive_turns)}
        onChange={(next) => save.mutate(next)}
      />
      <SpeakerFiles
        jobId={jobId}
        source={data.source}
        files={data.files}
        split={data.split}
        speakers={data.speakers}
        onSplitQueued={onSplitQueued}
      />
      {splitting && !data.split ? <UIText variant="caption">{t('speakers.split.running')}</UIText> : null}
    </UIStack>
  )
}

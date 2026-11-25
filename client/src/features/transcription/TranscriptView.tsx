import { useMutation, useQuery } from '@tanstack/react-query'
import { openPath } from '@tauri-apps/plugin-opener'
import { useState } from 'react'

import { useApi } from '@/shared/api/context'
import { UIButton } from '@/shared/components/atoms/UIButton'
import { UIMedia } from '@/shared/components/atoms/UIMedia'
import { UISkeleton } from '@/shared/components/atoms/UISkeleton'
import { UIStack } from '@/shared/components/atoms/UIStack'
import { UISwitch } from '@/shared/components/atoms/UISwitch'
import { UIText } from '@/shared/components/atoms/UIText'
import { UISpeakerLegend, type SpeakerMap } from '@/shared/components/molecules/UISpeakerLegend'
import { useSaveSpeakers } from '@/shared/hooks/useSpeakers'
import { t } from '@/shared/i18n/t'
import { useSyncedMedia } from '@/shared/media/useSyncedMedia'
import { openSection } from '@/shared/navigation/hash'

interface Word {
  start: number
  end: number
  word: string
  probability: number
  speaker?: string | null
}

interface Segment {
  start: number
  end: number
  text: string
  speaker?: string | null
  words: Word[]
}

/** La transcripción de un trabajo (GET /jobs/{id}/transcript): sus segmentos con hablante y los nombres. */
interface Transcript {
  source: string
  duration: number | null
  segments: Segment[]
  speakers: SpeakerMap
}

/** Un bloque: las palabras seguidas de un mismo hablante, como en un acta (spec 036, D-3). */
interface Block {
  speaker: string | null
  words: Word[]
}

/** Agrupa las palabras en bloques, uno por cambio de hablante. */
function blocksOf(segments: Segment[]): Block[] {
  const blocks: Block[] = []
  for (const word of segments.flatMap((segment) => segment.words)) {
    const speaker = word.speaker ?? null
    const last = blocks[blocks.length - 1]
    if (last && last.speaker === speaker) last.words.push(word)
    else blocks.push({ speaker, words: [word] })
  }
  return blocks
}

/** El tiempo que habla cada hablante, en segundos, para la leyenda. */
function secondsOf(segments: Segment[]): Record<string, number> {
  const totals: Record<string, number> = {}
  for (const word of segments.flatMap((segment) => segment.words)) {
    if (!word.speaker) continue
    totals[word.speaker] = (totals[word.speaker] ?? 0) + (word.end - word.start)
  }
  return totals
}

/** La carpeta de un archivo: lo que queda antes de su última barra. */
function folderOf(path: string): string {
  return path.replace(/[\\/][^\\/]*$/, '')
}

/**
 * El resultado de una transcripción (spec 036, AC-4 a AC-7): el reproductor, el texto por bloques con el nombre y el
 * color de cada hablante (una palabra lleva el reproductor a su tiempo), la leyenda editable, el TXT y los subtítulos.
 * Sin hablantes, muestra un párrafo por segmento.
 */
export function TranscriptView({ jobId }: { jobId: number }): React.JSX.Element {
  const api = useApi()
  const transcript = useQuery({
    queryKey: ['transcript', jobId],
    queryFn: () => api.get<Transcript>(`/jobs/${jobId}/transcript`),
  })
  const [media, setMedia] = useState<HTMLMediaElement | null>(null)
  const player = useSyncedMedia(media)
  const save = useSaveSpeakers(jobId)
  const [timestamps, setTimestamps] = useState(false)
  const [exported, setExported] = useState<string | null>(null)

  const exportText = useMutation({
    mutationFn: () => api.post<{ path: string }>(`/jobs/${jobId}/transcript/export`, { timestamps }),
    onSuccess: (result) => setExported(result.path),
  })
  const toSubtitles = useMutation({
    mutationFn: () => api.post<{ id: number }>('/subtitles/from-transcript', { job_id: jobId }),
    onSuccess: (project) => openSection('subtitles', { project: String(project.id) }),
  })

  if (transcript.isPending) return <UISkeleton className="h-64 w-full rounded-xl" />
  if (transcript.isError || !transcript.data) {
    return (
      <UIText variant="caption" className="text-destructive">
        {t('transcription.read_failed')}
      </UIText>
    )
  }
  const data = transcript.data
  if (data.segments.length === 0) return <UIText variant="caption">{t('transcription.empty')}</UIText>
  const withSpeakers = Object.keys(data.speakers).length > 0

  return (
    <UIStack gap="md">
      <UIMedia kind="video" src={api.fileUrl(data.source)} controls className="w-full rounded-lg" mediaRef={setMedia} />
      {withSpeakers ? (
        <UISpeakerLegend
          speakers={data.speakers}
          durations={secondsOf(data.segments)}
          onChange={(next) => save.mutate(next)}
        />
      ) : null}
      <UIStack gap="md">
        {withSpeakers
          ? blocksOf(data.segments).map((block, index) => {
              const speaker = block.speaker ? data.speakers[block.speaker] : undefined
              return (
                <UIStack key={index}
                  className="border-l-4 pl-3"
                  style={{ borderLeftColor: speaker?.color ?? 'transparent' }}
                >
                  <UIText variant="heading">{speaker?.name ?? ''}</UIText>
                  <UIText variant="body" className="leading-relaxed">
                    {block.words.map((word, position) => {
                      const active = player.time >= word.start && player.time < word.end
                      return (
                        <UIButton
                          key={position}
                          variant="ghost"
                          aria-current={active ? 'true' : undefined}
                          onClick={() => player.seek(word.start)}
                          className={`h-auto min-h-0 rounded px-0.5 py-0 ${active ? 'bg-muted' : ''}`}
                        >
                          {word.word.trim()}
                        </UIButton>
                      )
                    })}
                  </UIText>
                </UIStack>
              )
            })
          : data.segments.map((segment, index) => (
              <UIText key={index} variant="body">
                {segment.text}
              </UIText>
            ))}
      </UIStack>
      <UIStack direction="row" align="center" gap="md" className="flex-wrap">
        <UISwitch
          variant="inline"
          label={t('transcription.export.timestamps')}
          checked={timestamps}
          onChange={setTimestamps}
        />
        <UIButton variant="secondary" disabled={exportText.isPending} onClick={() => exportText.mutate()}>
          {t('transcription.export.txt')}
        </UIButton>
        {exported ? (
          <UIButton variant="ghost" onClick={() => void openPath(folderOf(exported))}>
            {t('transcription.open_folder')}
          </UIButton>
        ) : null}
        <UIButton disabled={toSubtitles.isPending} onClick={() => toSubtitles.mutate()}>
          {t('transcription.to_subtitles')}
        </UIButton>
      </UIStack>
      {exported ? <UIText variant="body">{t('transcription.exported', { path: exported })}</UIText> : null}
    </UIStack>
  )
}

import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'

import { useApi } from '@/shared/api/context'
import type { components } from '@/shared/api/schema'
import { UIProgress } from '@/shared/components/atoms/UIProgress'
import { UISkeleton } from '@/shared/components/atoms/UISkeleton'
import { UIStack } from '@/shared/components/atoms/UIStack'
import { UIText } from '@/shared/components/atoms/UIText'
import { useFromJob } from '@/shared/hooks/useFromJob'
import { t } from '@/shared/i18n/t'

import { TranscriptionForm } from './TranscriptionForm'
import { TranscriptView } from './TranscriptView'

type Job = components['schemas']['Job']
const FINISHED = ['done', 'error', 'cancelled']

/**
 * La sección Transcripción (spec 036, D-1 y D-5): el título, el formulario y, debajo, el progreso del trabajo recién
 * encolado o el resultado de un trabajo abierto con `?from_job=`.
 */
export function TranscriptionPage(): React.JSX.Element {
  const from = useFromJob()
  const [queued, setQueued] = useState<number | null>(null)
  const shown = from?.kind === 'transcribe' ? from.id : queued
  return (
    <UIStack gap="lg">
      <UIText variant="subtitle">{t('transcription.title')}</UIText>
      <TranscriptionForm onQueued={setQueued} />
      {shown !== null ? <JobResult jobId={shown} /> : null}
    </UIStack>
  )
}

function JobResult({ jobId }: { jobId: number }): React.JSX.Element {
  const api = useApi()
  const job = useQuery({
    queryKey: ['jobs', jobId],
    queryFn: () => api.get<Job>(`/jobs/${jobId}`),
    refetchInterval: (query) => (query.state.data && FINISHED.includes(query.state.data.status) ? false : 1000),
  })
  if (!job.data) return <UISkeleton className="h-32 w-full rounded-xl" />
  if (job.data.status === 'done') return <TranscriptView jobId={jobId} />
  if (FINISHED.includes(job.data.status)) {
    return (
      <UIText variant="caption" className="text-destructive">
        {t('transcription.job_failed')}
      </UIText>
    )
  }
  return <UIProgress value={job.data.progress} label={t('transcription.progress')} />
}

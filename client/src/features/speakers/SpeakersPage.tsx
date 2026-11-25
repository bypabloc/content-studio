import { UIStack } from '@/shared/components/atoms/UIStack'
import { UIText } from '@/shared/components/atoms/UIText'
import { useFromJob } from '@/shared/hooks/useFromJob'
import { t } from '@/shared/i18n/t'
import { useState } from 'react'

import { SpeakerResult } from './SpeakerResult'
import { SpeakersForm } from './SpeakersForm'

/**
 * La sección Hablantes (spec 037, D-1 y AC-7): el título y el formulario y, debajo, el resultado del trabajo recién
 * encolado o el de un trabajo abierto con `?from_job=` (sin volver a identificar hablantes).
 */
export function SpeakersPage(): React.JSX.Element {
  const from = useFromJob()
  const [queued, setQueued] = useState<number | null>(null)
  const shown = from?.kind === 'diarize' ? from.id : queued
  return (
    <UIStack gap="lg">
      <UIText variant="subtitle">{t('speakers.title')}</UIText>
      <SpeakersForm onQueued={setQueued} />
      {shown !== null ? <SpeakerResult jobId={shown} /> : null}
    </UIStack>
  )
}

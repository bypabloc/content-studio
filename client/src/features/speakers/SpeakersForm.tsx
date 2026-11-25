import { useMutation } from '@tanstack/react-query'
import { open } from '@tauri-apps/plugin-dialog'
import { useState } from 'react'

import { useApi } from '@/shared/api/context'
import { UIButton } from '@/shared/components/atoms/UIButton'
import { UIStack } from '@/shared/components/atoms/UIStack'
import { UIText } from '@/shared/components/atoms/UIText'
import { UIField } from '@/shared/components/molecules/UIField'
import { type SpeakerCounts, UISpeakerCountField } from '@/shared/components/molecules/UISpeakerCountField'
import { t } from '@/shared/i18n/t'

/**
 * Formulario de la sección Hablantes (spec 037, AC-1): el archivo y cuántos hablantes hay (automático, exacto o un
 * rango). Encola `diarize` con esos datos y avisa del trabajo con `onQueued`.
 */
export function SpeakersForm({ onQueued }: { onQueued: (jobId: number) => void }): React.JSX.Element {
  const api = useApi()
  const [input, setInput] = useState('')
  const [counts, setCounts] = useState<SpeakerCounts>({})

  const queue = useMutation({
    mutationFn: () => api.post<{ id: number }>('/jobs', { kind: 'diarize', params: { input, ...counts } }),
    onSuccess: (job) => onQueued(job.id),
  })

  async function choose(): Promise<void> {
    const picked = await open({ multiple: false, directory: false })
    if (typeof picked === 'string') setInput(picked)
  }

  return (
    <UIStack gap="md">
      <UIStack direction="row" align="end" gap="sm">
        <UIStack className="min-w-0 flex-1">
          <UIField label={t('transcription.file')} value={input} onChange={(event) => setInput(event.target.value)} />
        </UIStack>
        <UIButton variant="secondary" onClick={() => void choose()}>
          {t('transcription.choose')}
        </UIButton>
      </UIStack>
      <UISpeakerCountField onChange={setCounts} />
      <UIStack direction="row" justify="end">
        <UIButton disabled={input.trim() === '' || queue.isPending} onClick={() => queue.mutate()}>
          {t('speakers.start')}
        </UIButton>
      </UIStack>
      {queue.isError ? (
        <UIText variant="caption" className="text-destructive">
          {t('speakers.failed')}
        </UIText>
      ) : null}
    </UIStack>
  )
}

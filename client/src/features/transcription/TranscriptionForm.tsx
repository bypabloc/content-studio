import { useMutation, useQuery } from '@tanstack/react-query'
import { open } from '@tauri-apps/plugin-dialog'
import { useState } from 'react'

import { useApi } from '@/shared/api/context'
import type { components } from '@/shared/api/schema'
import { UIButton } from '@/shared/components/atoms/UIButton'
import { UILink } from '@/shared/components/atoms/UILink'
import { UIStack } from '@/shared/components/atoms/UIStack'
import { UISwitch } from '@/shared/components/atoms/UISwitch'
import { UIText } from '@/shared/components/atoms/UIText'
import { UIField } from '@/shared/components/molecules/UIField'
import { UISelect } from '@/shared/components/molecules/UISelect'
import { type SpeakerCounts, UISpeakerCountField } from '@/shared/components/molecules/UISpeakerCountField'
import { UIWhisperModelSelect } from '@/shared/components/molecules/UIWhisperModelSelect'
import { useRecommendedValue } from '@/shared/hooks/useRecommendedValue'
import { useSetting } from '@/shared/hooks/useSetting'
import { type MessageKey, t } from '@/shared/i18n/t'

type EngineInfo = components['schemas']['EngineInfo']

/** Los idiomas de la transcripción: los mismos que el Limpiador; «auto» deja que el modelo detecte el idioma. */
const LANGUAGES = ['auto', 'es', 'en', 'pt', 'fr', 'de', 'it'] as const

/**
 * Formulario de Transcripción (spec 036, AC-2 y AC-3): el archivo, el modelo y el idioma (los dos se recuerdan), y el
 * interruptor de hablantes. Sin el motor de hablantes, el interruptor está apagado y enlaza a Motores. Encola
 * `transcribe` y avisa del trabajo con `onQueued`.
 */
export function TranscriptionForm({ onQueued }: { onQueued: (jobId: number) => void }): React.JSX.Element {
  const api = useApi()
  const engines = useQuery({ queryKey: ['engines'], queryFn: () => api.get<EngineInfo[]>('/engines') })
  const whisper = engines.data?.find((engine) => engine.engine === 'faster-whisper')
  const modelOptions = (whisper?.models ?? []).map((model) => ({
    value: model.model,
    label: model.model,
    recommended: model.recommended,
  }))
  const [model] = useRecommendedValue('select.whisper.model', modelOptions)
  const [language, setLanguage] = useSetting<string>('select.transcription.language', 'auto')
  const pyannote = engines.data?.find((engine) => engine.engine === 'pyannote')
  const speakersAvailable = pyannote?.status === 'installed'

  const [input, setInput] = useState('')
  const [speakers, setSpeakers] = useState(false)
  const [counts, setCounts] = useState<SpeakerCounts>({})

  const queue = useMutation({
    mutationFn: () =>
      api.post<{ id: number }>('/jobs', {
        kind: 'transcribe',
        params: {
          input,
          model,
          language,
          ...(speakers && speakersAvailable ? { diarize: true, ...counts } : {}),
        },
      }),
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
      <UIWhisperModelSelect />
      <UISelect
        label={t('transcription.language')}
        value={language}
        options={LANGUAGES.map((code) => ({ value: code, label: t(`cleaner.language.${code}` as MessageKey) }))}
        onChange={(value) => setLanguage(value)}
      />
      <UISwitch
        label={t('transcription.diarize')}
        description={speakersAvailable ? undefined : t('transcription.diarize.missing')}
        checked={speakers && speakersAvailable}
        disabled={!speakersAvailable}
        onChange={setSpeakers}
      />
      {!speakersAvailable ? (
        <UILink href="#/engines" variant="inline" className="underline">
          {t('transcription.diarize.engines')}
        </UILink>
      ) : null}
      {speakers && speakersAvailable ? <UISpeakerCountField onChange={setCounts} /> : null}
      <UIStack direction="row" justify="end">
        <UIButton disabled={input.trim() === '' || queue.isPending} onClick={() => queue.mutate()}>
          {t('transcription.start')}
        </UIButton>
      </UIStack>
      {queue.isError ? (
        <UIText variant="caption" className="text-destructive">
          {t('transcription.failed')}
        </UIText>
      ) : null}
    </UIStack>
  )
}

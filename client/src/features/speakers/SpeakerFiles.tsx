import { useMutation } from '@tanstack/react-query'
import { openPath } from '@tauri-apps/plugin-opener'

import { useApi } from '@/shared/api/context'
import { UIButton } from '@/shared/components/atoms/UIButton'
import { UIMedia } from '@/shared/components/atoms/UIMedia'
import { UIStack } from '@/shared/components/atoms/UIStack'
import { UIText } from '@/shared/components/atoms/UIText'
import type { SpeakerMap } from '@/shared/components/molecules/UISpeakerLegend'
import { t } from '@/shared/i18n/t'
import { openSection } from '@/shared/navigation/hash'

/** Los archivos de turnos de una identificación de hablantes, con su ruta absoluta (spec 035, AC-3). */
export interface DiarizationFiles {
  json: string
  rttm: string
  csv: string
}

/** El nombre de un archivo sin su carpeta: funciona con rutas de Windows y de POSIX. */
function baseName(path: string): string {
  return path.replace(/^.*[\\/]/, '')
}

/** La carpeta de un archivo: lo que queda antes de su última barra. */
function folderOf(path: string): string {
  return path.replace(/[\\/][^\\/]*$/, '')
}

export interface SpeakerFilesProps {
  jobId: number
  source: string
  files: DiarizationFiles
  split: Record<string, string> | null
  speakers: SpeakerMap
  onSplitQueued?: (jobId: number) => void
}

/**
 * Los archivos de turnos con «Abrir carpeta» (AC-4), «Un audio por hablante» (AC-5) con un reproductor por hablante, y
 * «Abrir en el Editor» (AC-6). Con un solo hablante no hay nada que separar: el botón no aparece.
 */
export function SpeakerFiles({ jobId, source, files, split, speakers, onSplitQueued }: SpeakerFilesProps): React.JSX.Element {
  const api = useApi()
  const folder = folderOf(files.json)
  const canSplit = Object.keys(speakers).length > 1

  const splitQueue = useMutation({
    mutationFn: () => api.post<{ id: number }>('/jobs', { kind: 'diarize.split', params: { input: source, turns: folder } }),
    onSuccess: (job) => onSplitQueued?.(job.id),
  })
  const toEditor = useMutation({
    mutationFn: () => api.post<{ project: string }>('/editor/projects/from-diarization', { job: jobId }),
    onSuccess: (created) => openSection('editor', { project: created.project }),
  })

  return (
    <UIStack gap="md">
      <UIText variant="subtitle">{t('speakers.files.title')}</UIText>
      <UIStack gap="xs">
        {[files.json, files.rttm, files.csv].map((path) => (
          <UIText key={path} variant="body">
            {baseName(path)}
          </UIText>
        ))}
      </UIStack>
      <UIStack direction="row" align="center" gap="sm" className="flex-wrap">
        <UIButton variant="ghost" onClick={() => void openPath(folder)}>
          {t('speakers.files.open_folder')}
        </UIButton>
        {canSplit ? (
          <UIButton variant="secondary" disabled={splitQueue.isPending} onClick={() => splitQueue.mutate()}>
            {t('speakers.split')}
          </UIButton>
        ) : null}
        <UIButton disabled={toEditor.isPending} onClick={() => toEditor.mutate()}>
          {t('speakers.to_editor')}
        </UIButton>
      </UIStack>
      {split ? (
        <UIStack gap="md">
          {Object.entries(split).map(([speaker, path]) => {
            const name = speakers[speaker]?.name ?? speaker
            return (
              <UIStack key={speaker} gap="xs">
                <UIText variant="heading">{name}</UIText>
                <UIMedia kind="audio" src={api.fileUrl(path)} controls className="w-full" label={name} />
              </UIStack>
            )
          })}
        </UIStack>
      ) : null}
    </UIStack>
  )
}

import { useState } from 'react'

import { t } from '@/shared/i18n/t'

import { UIStack } from '../../atoms/UIStack'
import { UIText } from '../../atoms/UIText'
import { Input } from '../../shadcn/input'

/** Nombre y color de un hablante, como los guarda speakers.json. */
export interface Speaker {
  name: string
  color: string
}

/** Todos los hablantes de un trabajo, por su id (SPEAKER_00, …). */
export type SpeakerMap = Record<string, Speaker>

const MAX_NAME = 40

/**
 * La leyenda de los hablantes: una fila por hablante con su color (un selector) y su nombre (editable). Guarda el mapa
 * entero al cambiar el color, y al salir del nombre si no está vacío. La reutilizan Transcripción (036), Hablantes (037) y
 * los demás lugares que muestran hablantes (038).
 */
export function UISpeakerLegend({
  speakers,
  durations,
  onChange,
}: {
  speakers: SpeakerMap
  durations?: Record<string, number>
  onChange: (next: SpeakerMap) => void
}): React.JSX.Element {
  return (
    <UIStack gap="sm" role="list" aria-label={t('speakers.legend.title')}>
      {Object.entries(speakers).map(([id, speaker]) => (
        <SpeakerRow
          key={id}
          speaker={speaker}
          seconds={durations?.[id]}
          onCommit={(next) => onChange({ ...speakers, [id]: next })}
        />
      ))}
    </UIStack>
  )
}

function SpeakerRow({
  speaker,
  seconds,
  onCommit,
}: {
  speaker: Speaker
  seconds?: number
  onCommit: (next: Speaker) => void
}): React.JSX.Element {
  const [draft, setDraft] = useState(speaker.name)
  const [synced, setSynced] = useState(speaker.name)
  // Un nombre que cambia desde fuera (otro guardado) reemplaza el borrador: se ajusta al render, sin efecto.
  if (synced !== speaker.name) {
    setSynced(speaker.name)
    setDraft(speaker.name)
  }

  function commitName(): void {
    const name = draft.trim()
    if (name.length < 1 || name.length > MAX_NAME) {
      setDraft(speaker.name)
      return
    }
    if (name !== speaker.name) onCommit({ ...speaker, name })
  }

  return (
    <UIStack direction="row" align="center" gap="sm" role="listitem">
      <Input
        type="color"
        value={speaker.color}
        aria-label={t('speakers.legend.color', { name: speaker.name })}
        onChange={(event) => onCommit({ ...speaker, color: event.target.value })}
        className="h-8 w-8 cursor-pointer rounded border-0 bg-transparent p-0"
      />
      <Input
        type="text"
        value={draft}
        maxLength={MAX_NAME}
        aria-label={t('speakers.legend.rename', { name: speaker.name })}
        onChange={(event) => setDraft(event.target.value)}
        onBlur={commitName}
        onKeyDown={(event) => {
          if (event.key === 'Enter') commitName()
        }}
        className="min-w-0 flex-1"
      />
      {seconds !== undefined ? (
        <UIText variant="caption">{t('speakers.legend.seconds', { seconds: seconds.toFixed(1) })}</UIText>
      ) : null}
    </UIStack>
  )
}

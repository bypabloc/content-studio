import { UIButton } from '@/shared/components/atoms/UIButton';
import { UIStack } from '@/shared/components/atoms/UIStack';
import { UIText } from '@/shared/components/atoms/UIText';
import { UIField } from '@/shared/components/molecules/UIField';
import { UIIconButton } from '@/shared/components/molecules/UIIconButton';
import { UISpeakerChip } from '@/shared/components/molecules/UISpeakerLegend';
import { UISelect } from '@/shared/components/molecules/UISelect';
import { t } from '@/shared/i18n/t';

import { deleteCue, mergeCues, setCueSpeaker, setCueText, splitCue, toggleKeyword, type DocEdit } from './cues';

// La palabra clave que marca un clic en su chip (D-9): el color de resaltado de las palabras clave.
const KEYWORD = { color: '#FF5555' };

/**
 * Los cues del documento: texto editable, dividir, unir y borrar, y las palabras como chips (un clic marca la clave).
 * Con hablantes, cada cue muestra su hablante y lo cambia desde su menú.
 */
export function CueList({ doc, onChange }: { doc: DocEdit; onChange: (next: DocEdit) => void }): React.JSX.Element {
  const speakers = doc.speakers ?? {};
  const speakerIds = Object.keys(speakers);
  return (
    <UIStack gap="md">
      {doc.cues.map((cue, index) => (
        <UIStack key={`${cue.id}-${index}`} gap="sm">
          <UIStack direction="row" gap="sm" align="center">
            <UIText variant="caption">{`${index + 1}`}</UIText>
            <UIField
              label={t('subtitles.cues.text')}
              hideLabel
              value={cue.text}
              onChange={(event) => onChange(setCueText(doc, index, event.target.value))}
            />
            {cue.speaker && speakers[cue.speaker] ? (
              <UISpeakerChip name={speakers[cue.speaker].name} color={speakers[cue.speaker].color} />
            ) : null}
            {speakerIds.length > 0 ? (
              <UISelect
                label={t('subtitles.cues.speaker')}
                hideLabel
                value={cue.speaker ?? ''}
                options={speakerIds.map((id) => ({ value: id, label: speakers[id].name }))}
                onChange={(value) => onChange(setCueSpeaker(doc, index, value))}
              />
            ) : null}
            <UIIconButton icon="scissors" label={t('subtitles.cues.split')} onClick={() => onChange(splitCue(doc, index))} />
            <UIIconButton icon="layers" label={t('subtitles.cues.merge')} onClick={() => onChange(mergeCues(doc, index))} />
            <UIIconButton icon="trash-2" label={t('subtitles.cues.delete')} onClick={() => onChange(deleteCue(doc, index))} />
          </UIStack>
          <UIStack direction="row" gap="sm">
            {cue.words.map((word, at) => (
              <UIButton
                key={`${at}-${word.text}`}
                variant={word.keyword ? 'primary' : 'secondary'}
                aria-pressed={Boolean(word.keyword)}
                onClick={() => onChange(toggleKeyword(doc, index, at, KEYWORD))}
              >
                {word.text}
              </UIButton>
            ))}
          </UIStack>
        </UIStack>
      ))}
    </UIStack>
  );
}

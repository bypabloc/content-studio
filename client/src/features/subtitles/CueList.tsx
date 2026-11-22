import { UIButton } from '@/shared/components/atoms/UIButton';
import { UIStack } from '@/shared/components/atoms/UIStack';
import { UIText } from '@/shared/components/atoms/UIText';
import { UIField } from '@/shared/components/molecules/UIField';
import { UIIconButton } from '@/shared/components/molecules/UIIconButton';
import { t } from '@/shared/i18n/t';

import { deleteCue, mergeCues, setCueText, splitCue, toggleKeyword, type DocEdit } from './cues';

// La palabra clave que marca un clic en su chip (D-9): el color de resaltado de las palabras clave.
const KEYWORD = { color: '#FF5555' };

/** Los cues del documento: texto editable, dividir, unir y borrar, y las palabras como chips (un clic marca la clave). */
export function CueList({ doc, onChange }: { doc: DocEdit; onChange: (next: DocEdit) => void }): React.JSX.Element {
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

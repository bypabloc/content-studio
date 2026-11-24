import { useState } from 'react';

import { AssistantButton } from '@/features/assistant/AssistantButton';
import { useAssistantStatus, useAssistantTask } from '@/features/assistant/useAssistant';
import { UIButton } from '@/shared/components/atoms/UIButton';
import { UIStack } from '@/shared/components/atoms/UIStack';
import { UIText } from '@/shared/components/atoms/UIText';
import { UITextarea } from '@/shared/components/molecules/UITextarea';
import { t } from '@/shared/i18n/t';

import type { FreeText } from './FreeTextStyle';

interface Caption {
  caption: string;
  key: string;
  bpm: number;
  time_signature: string;
}

/**
 * «Describir en español» (spec 021, D-5): el asistente pasa la descripción al caption en inglés de ACE-Step, con
 * tonalidad, BPM y compás. Es una sugerencia: «Usar la sugerencia» llena el texto libre, que sigue editable.
 */
export function DescribeMusic({ onApply }: { onApply: (value: FreeText) => void }): React.JSX.Element | null {
  const [description, setDescription] = useState('');
  const task = useAssistantTask<Caption>('llm.music_caption');
  const status = useAssistantStatus();
  const suggestion = task.result;
  if (!status.data?.enabled) return null;
  return (
    <UIStack gap="sm">
      <UITextarea
        label={t('llm.describe.label')}
        value={description}
        onChange={(event) => setDescription(event.target.value)}
        className="min-h-20"
      />
      <AssistantButton
        label={t('llm.button.describe')}
        busy={task.busy}
        error={task.error}
        disabled={!description.trim()}
        onClick={() => task.run({ description })}
      />
      {suggestion ? (
        <UIStack gap="sm">
          <UIText variant="body">
            {t('llm.describe.result', {
              caption: suggestion.caption,
              key: suggestion.key,
              bpm: suggestion.bpm,
              signature: suggestion.time_signature,
            })}
          </UIText>
          <UIButton
            variant="primary"
            className="self-start"
            onClick={() =>
              onApply({ caption: suggestion.caption, key: suggestion.key, bpm: suggestion.bpm, timeSignature: suggestion.time_signature })
            }
          >
            {t('llm.describe.use')}
          </UIButton>
        </UIStack>
      ) : null}
    </UIStack>
  );
}

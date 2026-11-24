import { useState } from 'react';

import { UIBadge } from '@/shared/components/atoms/UIBadge';
import { UIButton } from '@/shared/components/atoms/UIButton';
import { UICheckbox } from '@/shared/components/atoms/UICheckbox';
import { UIStack } from '@/shared/components/atoms/UIStack';
import { type MessageKey, t } from '@/shared/i18n/t';

export interface SuggestionRow {
  id: number;
  content: React.ReactNode;
  flag?: string | null;
  checked?: boolean;
}

interface Props {
  title: string;
  rows: SuggestionRow[];
  /** Sin elección por cue (la traducción entra como una pista entera). */
  selectable?: boolean;
  busy: boolean;
  onApply: (accepted: number[] | null) => void;
}

/** Las sugerencias por cue (spec 021, D-5): elegir cuáles aplicar, o todas; las marcadas para revisar empiezan sin elegir. */
export function CueSuggestions({ title, rows, selectable = true, busy, onApply }: Props): React.JSX.Element {
  const [chosen, setChosen] = useState(() => new Set(rows.filter((row) => row.checked !== false).map((row) => row.id)));
  const toggle = (id: number, on: boolean) =>
    setChosen((current) => {
      const next = new Set(current);
      if (on) next.add(id);
      else next.delete(id);
      return next;
    });
  return (
    <UIStack role="region" aria-label={title} gap="sm">
      {rows.map((row) => (
        <UIStack key={row.id} direction="row" align="center" gap="sm" className="flex-wrap">
          {selectable ? (
            <UICheckbox label={t('llm.subtitles.cue', { id: row.id })} checked={chosen.has(row.id)} onChange={(on) => toggle(row.id, on)} />
          ) : null}
          {row.content}
          {row.flag ? <UIBadge>{t(`llm.subtitles.flag.${row.flag}` as MessageKey)}</UIBadge> : null}
        </UIStack>
      ))}
      <UIStack direction="row" gap="sm" className="flex-wrap">
        {selectable ? (
          <UIButton variant="primary" disabled={busy || chosen.size === 0} onClick={() => onApply([...chosen])}>
            {t('llm.apply_selected')}
          </UIButton>
        ) : null}
        <UIButton variant={selectable ? 'secondary' : 'primary'} disabled={busy} onClick={() => onApply(selectable ? rows.map((row) => row.id) : null)}>
          {selectable ? t('llm.accept_all') : t('llm.subtitles.accept_track')}
        </UIButton>
      </UIStack>
    </UIStack>
  );
}

import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';

import { AssistantButton } from '@/features/assistant/AssistantButton';
import { useAssistantStatus, useAssistantTask } from '@/features/assistant/useAssistant';
import { useApi } from '@/shared/api/context';
import { UICard } from '@/shared/components/atoms/UICard';
import { UICheckbox } from '@/shared/components/atoms/UICheckbox';
import { UIStack } from '@/shared/components/atoms/UIStack';
import { UIText } from '@/shared/components/atoms/UIText';
import { UIIconButton } from '@/shared/components/molecules/UIIconButton';
import { type MessageKey, t } from '@/shared/i18n/t';

import type { LibraryItem } from './types';

const PLATFORMS = ['youtube', 'reels', 'tiktok'] as const;

interface Proposal {
  titles: string[];
  description: string;
  hashtags: string[];
  chapters?: { t: number; title: string }[];
}
interface Publish {
  platforms: Record<string, Proposal>;
}

/** 0:00, 1:05, 12:30: el formato de los capítulos de YouTube. */
export function clock(seconds: number): string {
  const whole = Math.round(seconds);
  return `${Math.floor(whole / 60)}:${String(whole % 60).padStart(2, '0')}`;
}

function Copyable({ label, text }: { label: string; text: string }): React.JSX.Element {
  return (
    <UIStack direction="row" align="center" gap="sm">
      <UIText variant="body" className="min-w-0 flex-1 whitespace-pre-line">
        {text}
      </UIText>
      <UIIconButton icon="copy" label={`${t('action.copy')}: ${label}`} onClick={() => void navigator.clipboard.writeText(text)} />
    </UIStack>
  );
}

/**
 * «Publicar» en el detalle de un video o audio (spec 021, D-5): elegir plataformas, generar con el asistente y copiar
 * cada campo. Lo último que se generó se lee de publish.json; «Generar» de nuevo lo regenera.
 */
export function PublishTab({ item }: { item: LibraryItem }): React.JSX.Element | null {
  const api = useApi();
  const [platforms, setPlatforms] = useState<string[]>(['youtube']);
  const saved = useQuery({
    queryKey: ['library', 'publish', item.id],
    queryFn: () => api.get<Publish>(`/library/${item.id}/publish`),
    retry: false,
  });
  const task = useAssistantTask<Publish>('llm.publish');
  const status = useAssistantStatus();
  const data = task.result ?? saved.data;
  const toggle = (platform: string, on: boolean) =>
    setPlatforms((current) => (on ? [...current, platform] : current.filter((value) => value !== platform)));
  if (!status.data?.enabled) return null;
  return (
    <UIStack role="region" aria-label={t('llm.publish.title')} gap="md">
      <UIText variant="subtitle">{t('llm.publish.title')}</UIText>
      <UIStack direction="row" gap="md" className="flex-wrap">
        {PLATFORMS.map((platform) => (
          <UICheckbox key={platform} label={t(`llm.platform.${platform}` as MessageKey)} checked={platforms.includes(platform)} onChange={(on) => toggle(platform, on)} />
        ))}
      </UIStack>
      <AssistantButton
        label={data ? t('llm.publish.again') : t('llm.button.publish')}
        busy={task.busy}
        error={task.error}
        disabled={platforms.length === 0}
        onClick={() => task.run({ item_id: item.id, platforms })}
      />
      {Object.entries(data?.platforms ?? {}).map(([platform, proposal]) => (
        <UICard key={platform}>
          <UIStack gap="sm">
            <UIText variant="subtitle">{t(`llm.platform.${platform}` as MessageKey)}</UIText>
            <UIText variant="caption">{t('llm.publish.titles')}</UIText>
            {proposal.titles.map((title) => (
              <Copyable key={title} label={title} text={title} />
            ))}
            <UIText variant="caption">{t('llm.publish.description')}</UIText>
            <Copyable label={t('llm.publish.description')} text={proposal.description} />
            <UIText variant="caption">{t('llm.publish.hashtags')}</UIText>
            <Copyable label={t('llm.publish.hashtags')} text={proposal.hashtags.join(' ')} />
            {proposal.chapters ? (
              <>
                <UIText variant="caption">{t('llm.publish.chapters')}</UIText>
                <Copyable
                  label={t('llm.publish.chapters')}
                  text={proposal.chapters.map((chapter) => `${clock(chapter.t)} ${chapter.title}`).join('\n')}
                />
              </>
            ) : null}
          </UIStack>
        </UICard>
      ))}
    </UIStack>
  );
}

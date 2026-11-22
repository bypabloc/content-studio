import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useEffect, useState } from 'react';

import { useApi } from '@/shared/api/context';
import { UIButton } from '@/shared/components/atoms/UIButton';
import { UIStack } from '@/shared/components/atoms/UIStack';
import { UIText } from '@/shared/components/atoms/UIText';
import { UISelect } from '@/shared/components/molecules/UISelect';
import { t } from '@/shared/i18n/t';

import { type StyleIn, toAss } from './ass';
import { CueList } from './CueList';
import { type DocEdit, mergeCues, splitCue } from './cues';
import { BUILTIN_PRESETS, recommendedPreset } from './presets';
import { StylePanel } from './StylePanel';
import { SubtitlesPreview } from './SubtitlesPreview';
import type { ZoneName } from './SafeZones';

const SAVE_DELAY_MS = 1000; // D-9: el guardado espera 1 s sin cambios

const ZONE_NAMES: Record<string, ZoneName | null> = { none: null, reels: 'reels', tiktok: 'tiktok', shorts: 'shorts' };

// Las teclas del editor no se disparan mientras se escribe un texto.
function isTyping(target: EventTarget | null): boolean {
  return target instanceof HTMLElement && (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.isContentEditable);
}

/**
 * El editor de un proyecto (D-9): la vista previa, los cues, el estilo y las acciones. Los cambios se guardan solos, 1 s
 * después del último, con un PUT del documento entero. M une el cue con el siguiente, S lo divide y ←/→ cambian de cue.
 */
export function SubtitlesEditor({ projectId }: { projectId: number }): React.JSX.Element {
  const api = useApi();
  const queryClient = useQueryClient();
  const query = useQuery({
    queryKey: ['subtitles', projectId],
    queryFn: () => api.get<DocEdit>(`/subtitles/${projectId}`),
  });
  const [draft, setDraft] = useState<DocEdit | null>(null);
  const [focus, setFocus] = useState(0);
  const [aspect, setAspect] = useState(16 / 9);
  const [zoneKey, setZoneKey] = useState('none');
  const doc = draft ?? query.data ?? null;

  useEffect(() => {
    if (!draft) return;
    const timer = window.setTimeout(() => void api.put(`/subtitles/${projectId}`, draft), SAVE_DELAY_MS);
    return () => window.clearTimeout(timer);
  }, [api, draft, projectId]);

  useEffect(() => {
    if (!doc) return;
    const current = doc;
    function onKey(event: KeyboardEvent) {
      if (isTyping(event.target)) return;
      if (event.key === 'm') setDraft(mergeCues(current, focus));
      if (event.key === 's') setDraft(splitCue(current, focus));
      if (event.key === 'ArrowLeft') setFocus((index) => Math.max(0, index - 1));
      if (event.key === 'ArrowRight') setFocus((index) => Math.min(current.cues.length - 1, index + 1));
    }
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [doc, focus]);

  async function enqueue(kind: 'subtitles.burn' | 'subtitles.translate') {
    // El trabajo lee el documento al arrancar: se guarda antes lo que aún espera el guardado.
    if (draft) await api.put(`/subtitles/${projectId}`, draft);
    await api.post('/jobs', { kind, params: { project_id: projectId } });
    void queryClient.invalidateQueries({ queryKey: ['jobs'] });
  }

  if (!doc) return <UIText variant="caption">{t('subtitles.editor.loading')}</UIText>;
  const style = Object.keys(doc.style).length > 0 ? (doc.style as unknown as StyleIn) : BUILTIN_PRESETS[recommendedPreset(aspect)];
  const playRes: [number, number] = aspect <= 1 ? [1080, 1920] : [1920, 1080];
  const ass = toAss(doc, style, playRes);

  return (
    <UIStack gap="md">
      <UISelect
        label={t('subtitles.editor.zone')}
        value={zoneKey}
        options={[
          { value: 'none', label: t('subtitles.zones.none') },
          { value: 'reels', label: t('subtitles.zones.reels') },
          { value: 'tiktok', label: t('subtitles.zones.tiktok') },
          { value: 'shorts', label: t('subtitles.zones.shorts') },
        ]}
        onChange={setZoneKey}
      />
      <SubtitlesPreview src={api.fileUrl(doc.source.path)} ass={ass} zone={ZONE_NAMES[zoneKey] ?? null} onAspect={setAspect} />
      <UIStack direction="row" gap="sm">
        <UIButton variant="secondary" onClick={() => void enqueue('subtitles.burn')}>
          {t('subtitles.editor.burn')}
        </UIButton>
        <UIButton variant="secondary" onClick={() => void enqueue('subtitles.translate')}>
          {t('subtitles.editor.translate')}
        </UIButton>
      </UIStack>
      <UIStack direction="row" gap="lg" align="start">
        <UIStack gap="md">
          <CueList doc={doc} onChange={setDraft} />
        </UIStack>
        <UIStack gap="md">
          <StylePanel
            style={style}
            aspect={aspect}
            onStyleChange={(next) => setDraft({ ...doc, style: next as unknown as Record<string, unknown> })}
          />
        </UIStack>
      </UIStack>
    </UIStack>
  );
}

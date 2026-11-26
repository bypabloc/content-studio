import { useQuery } from '@tanstack/react-query';

import { useApi } from '@/shared/api/context';
import { UIStack } from '@/shared/components/atoms/UIStack';
import { UIText } from '@/shared/components/atoms/UIText';
import type { SpeakerMap } from '@/shared/components/molecules/UISpeakerLegend';

import { timeToPx } from '../model/timeline';

type LaneCue = { id: number; start: number; end: number; text: string; speaker?: string | null };
type LaneDoc = { cues: LaneCue[]; speakers?: SpeakerMap };

/**
 * Un bloque por cue del proyecto de subtítulos de la pista (AC-7): en la escala de la línea de tiempo, con el color y el
 * nombre de su hablante; un cue sin hablante queda neutro. Lee el proyecto con `GET /subtitles/{id}`.
 */
export function SubtitleLane({ projectId, zoom }: { projectId: string; zoom: number }): React.JSX.Element {
  const api = useApi();
  const project = useQuery({
    queryKey: ['subtitles', projectId],
    queryFn: () => api.get<LaneDoc>(`/subtitles/${projectId}`),
  });
  return (
    <>
      {(project.data?.cues ?? []).map((cue) => {
        const speaker = cue.speaker ? project.data?.speakers?.[cue.speaker] : undefined;
        return (
          <UIStack
            key={cue.id}
            role="group"
            aria-label={cue.text}
            gap="xs"
            className={`absolute overflow-hidden rounded-md px-1 py-0.5 text-foreground ${speaker ? '' : 'bg-muted'}`}
            style={{
              left: `${timeToPx(cue.start, zoom)}px`,
              width: `${timeToPx(cue.end - cue.start, zoom)}px`,
              top: '4px',
              height: '40px',
              backgroundColor: speaker?.color,
            }}
          >
            {speaker ? <UIText variant="caption">{speaker.name}</UIText> : null}
          </UIStack>
        );
      })}
    </>
  );
}

import { t } from '@/shared/i18n/t';

import type { Op, Track } from './model/types';

export type ImportFile = {
  source: string;
  duration: number;
  kind: 'audio' | 'video' | 'image';
  has_audio: boolean;
};

/** Construye las operaciones para importar clips multimedia y enlazar el audio de cada video. */
export function buildImportOperations(
  files: ImportFile[],
  existingTracks: Track[],
  trackCount: number,
  targetTrack: string | undefined,
  start: number,
): Op[] {
  const operations: Op[] = [];
  const tracks: Partial<Record<'audio' | 'video', string>> = {};
  let addedTracks = 0;
  const ensureTrack = (kind: 'audio' | 'video'): string => {
    const existing = targetTrack
      ? existingTracks.find((track) => track.id === targetTrack && track.kind === kind && !track.locked)
      : undefined;
    if (existing) return existing.id;
    if (tracks[kind]) return tracks[kind]!;
    const id = `track-${crypto.randomUUID()}`;
    const name = t('editor.track.new_name', { n: trackCount + addedTracks + 1 });
    const track = kind === 'video'
      ? { id, kind, name, opacity: 1, hidden: false, locked: false, height: 80 }
      : { id, kind, name, volume_db: 0, mute: false, solo: false, locked: false, height: 80 };
    const firstAudio = existingTracks.findIndex((item) => item.kind === 'audio');
    operations.push({
      type: 'addTrack',
      track,
      ...(kind === 'video' && firstAudio >= 0 ? { index: firstAudio } : {}),
    });
    addedTracks += 1;
    tracks[kind] = id;
    return id;
  };
  let cursor = Math.max(0, start);

  for (const file of files) {
    if (file.kind === 'image' || file.kind === 'video') {
      const link = file.kind === 'video' && file.has_audio ? crypto.randomUUID() : undefined;
      operations.push({
        type: 'addClip',
        clip: {
          id: crypto.randomUUID(),
          track: ensureTrack('video'),
          src: file.source,
          src_in: 0,
          src_out: file.duration,
          start: cursor,
          fade_in: 0,
          fade_out: 0,
          media: file.kind,
          transform: {
            x: 0,
            y: 0,
            scale_x: 1,
            scale_y: 1,
            rotation: 0,
            opacity: 1,
            crop: { l: 0, t: 0, r: 0, b: 0 },
            anchor_x: 0.5,
            anchor_y: 0.5,
          },
          keyframes: {},
          ...(link ? { link } : {}),
        },
      });
      if (link) {
        operations.push({
          type: 'addClip',
          clip: {
            id: crypto.randomUUID(),
            track: ensureTrack('audio'),
            src: file.source,
            src_in: 0,
            src_out: file.duration,
            start: cursor,
            gain_db: 0,
            fade_in: 0,
            fade_out: 0,
            link,
          },
        });
      }
    } else {
      operations.push({
        type: 'addClip',
        clip: {
          id: crypto.randomUUID(),
          track: ensureTrack('audio'),
          src: file.source,
          src_in: 0,
          src_out: file.duration,
          start: cursor,
          gain_db: 0,
          fade_in: 0,
          fade_out: 0,
        },
      });
    }
    cursor += file.duration;
  }

  return operations;
}

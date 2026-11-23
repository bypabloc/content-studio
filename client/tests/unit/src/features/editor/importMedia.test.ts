import { describe, expect, it } from 'vitest';

import { buildImportOperations } from '@/features/editor/importMedia';
import type { Track } from '@/features/editor/model/types';
import { t } from '@/shared/i18n/t';

const AUDIO_TRACK: Track = {
  id: 'voice', kind: 'audio', name: 'Voz', volume_db: 0, mute: false, solo: false, locked: false, height: 80,
};

describe('buildImportOperations', () => {
  it('crea clips visuales y enlaza el audio del video en un grupo', () => {
    const operations = buildImportOperations(
      [
        { source: 'logo.png', duration: 5, kind: 'image', has_audio: false },
        { source: 'scene.mp4', duration: 3, kind: 'video', has_audio: true },
      ],
      [AUDIO_TRACK],
      1,
      undefined,
      2,
    );
    const visual = operations.flatMap((operation) => operation.type === 'addClip' && operation.clip.media ? [operation.clip] : []);
    const audio = operations.flatMap((operation) => operation.type === 'addClip' && !operation.clip.media ? [operation.clip] : []);
    const videoTrack = operations.find((operation) => operation.type === 'addTrack' && operation.track.kind === 'video');
    const audioTrack = operations.find((operation) => operation.type === 'addTrack' && operation.track.kind === 'audio');

    expect(videoTrack?.type === 'addTrack' && videoTrack.track.kind === 'video' ? videoTrack.track : null).toMatchObject({
      kind: 'video', name: t('editor.track.new_name', { n: 2 }), opacity: 1, hidden: false,
    });
    expect(audioTrack?.type === 'addTrack' && audioTrack.track.kind === 'audio' ? audioTrack.track : null).toMatchObject({
      kind: 'audio', name: t('editor.track.new_name', { n: 3 }), volume_db: 0,
    });
    expect(visual.map(({ src, start, src_out, media }) => ({ src, start, src_out, media }))).toEqual([
      { src: 'logo.png', start: 2, src_out: 5, media: 'image' },
      { src: 'scene.mp4', start: 7, src_out: 3, media: 'video' },
    ]);
    expect(audio).toHaveLength(1);
    expect(audio[0]).toMatchObject({ src: 'scene.mp4', start: 7, src_out: 3, gain_db: 0 });
    expect(audio[0].link).toBe(visual[1].link);
    expect(audio[0].link).toBeTruthy();
  });

  it('mantiene el video sin audio en la pista visual solicitada y no crea un clip de audio', () => {
    const videoTrack: Track = { id: 'video', kind: 'video', name: 'Video', opacity: 1, hidden: false, locked: false };
    const operations = buildImportOperations(
      [{ source: 'silent.mp4', duration: 4, kind: 'video', has_audio: false }],
      [AUDIO_TRACK, videoTrack],
      2,
      videoTrack.id,
      6,
    );

    expect(operations).toHaveLength(1);
    expect(operations[0]).toMatchObject({
      type: 'addClip', clip: { media: 'video', track: 'video', start: 6, src_out: 4 },
    });
  });
});

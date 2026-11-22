import { describe, expect, it } from 'vitest';

import type { MixProject, SlotKey } from '@/features/mix/types';

describe('tipos de Mezcla (spec 016, D-3)', () => {
  it('un proyecto trae sus rutas, sus regiones y los parámetros del server', () => {
    const slots: SlotKey[] = ['voice', 'music', 'video'];
    const project: MixProject = {
      id: 1,
      name: 'charla',
      voice: 'voz.wav',
      music: 'musica.wav',
      video: null,
      video_mode: 'replace',
      regions: [[1, 2]],
      params: {
        mode: 'transcript',
        duck_db: -12,
        ramp_ms: 300,
        music_db: -6,
        voice_db: 0,
        intro: 0,
        outro: 0,
        lufs: -14,
        merge_gap: 0.6,
        pre: 0.2,
        post: 0.4,
      },
      transcribe_job: null,
      status: 'ready',
    };

    expect(slots).toHaveLength(3);
    expect(project.regions).toEqual([[1, 2]]);
  });
});

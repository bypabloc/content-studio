/** Lo que el server devuelve de un proyecto de mezcla (`/mix/{id}`, spec 016, D-3). */
export interface MixParams {
  mode: string;
  duck_db: number;
  ramp_ms: number;
  music_db: number;
  voice_db: number;
  intro: number;
  outro: number;
  lufs: number;
  merge_gap: number;
  pre: number;
  post: number;
}

export interface MixProject {
  id: number;
  name: string;
  voice: string;
  music: string;
  video: string | null;
  video_mode: string;
  regions: [number, number][];
  params: MixParams;
  transcribe_job: number | null;
  status: 'ready' | 'transcribing' | 'failed';
}

export type SlotKey = 'voice' | 'music' | 'video';

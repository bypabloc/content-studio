import { open } from '@tauri-apps/plugin-dialog';

import { useApi } from '@/shared/api/context';
import { UIButton } from '@/shared/components/atoms/UIButton';
import { UIStack } from '@/shared/components/atoms/UIStack';
import { UIText } from '@/shared/components/atoms/UIText';
import { type JobRow, UIJobPicker } from '@/shared/components/molecules/UIJobPicker';
import { t } from '@/shared/i18n/t';

import type { SlotKey } from './types';

const AUDIO = ['wav', 'mp3', 'm4a', 'flac', 'ogg', 'aac'];
const VIDEO = ['mp4', 'mov', 'mkv', 'webm'];
// Los trabajos que dejan una pista de cada ranura: narraciones para la voz, música, y videos para el video.
const KINDS: Record<SlotKey, string[]> = {
  voice: ['narration'],
  music: ['music'],
  video: ['clean.render', 'media.convert', 'subtitles.burn'],
};

const suffixOf = (path: string): string => path.slice(path.lastIndexOf('.') + 1).toLowerCase();

export interface MixSlotProps {
  slot: SlotKey;
  value: string | null;
  onPick: (path: string) => void;
}

/**
 * Una ranura de la mezcla (voz, música o video): la ruta elegida y sus dos orígenes, «Archivo…» y «Del historial»
 * (spec 016, D-4). El historial lleva el primer archivo de la clase de la ranura que dejó el trabajo.
 */
export function MixSlot({ slot, value, onPick }: MixSlotProps): React.JSX.Element {
  const api = useApi();
  const extensions = slot === 'video' ? VIDEO : AUDIO;

  async function pickFile(): Promise<void> {
    const chosen = await open({ multiple: false, filters: [{ name: t('mix.file.filter'), extensions }] });
    if (typeof chosen === 'string') onPick(chosen);
  }

  async function pickJob(job: JobRow): Promise<void> {
    const outputs = await api.get<string[]>(`/jobs/${job.id}/outputs`);
    const match = outputs.find((path) => extensions.includes(suffixOf(path)));
    if (match) onPick(match);
  }

  // Las claves van escritas enteras para que la etapa i18n las vea como usadas.
  const titles: Record<SlotKey, string> = {
    voice: t('mix.slot.voice'),
    music: t('mix.slot.music'),
    video: t('mix.slot.video'),
  };
  return (
    <UIStack role="group" aria-label={titles[slot]} gap="sm">
      <UIText variant="body">{value ?? t('mix.slot.empty')}</UIText>
      <UIStack direction="row" gap="sm" align="center">
        <UIButton variant="secondary" onClick={() => void pickFile()}>
          {t('mix.source.file')}
        </UIButton>
        <UIJobPicker kinds={KINDS[slot]} label={t('mix.source.history')} onPick={(job) => void pickJob(job)} />
      </UIStack>
    </UIStack>
  );
}

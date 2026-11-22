import { useEffect, useRef, useState } from 'react';

import { useApi } from '@/shared/api/context';
import type { Job } from '@/shared/api/events';
import { UIButton } from '@/shared/components/atoms/UIButton';
import { UIIconButton } from '@/shared/components/molecules/UIIconButton';
import { UIMedia } from '@/shared/components/atoms/UIMedia';
import { UIStack } from '@/shared/components/atoms/UIStack';
import { UIText } from '@/shared/components/atoms/UIText';
import { useSyncedMedia } from '@/shared/media/useSyncedMedia';
import { t } from '@/shared/i18n/t';
import { baseName, isVideoPath } from '@/shared/media/formats';

type Version = 'original' | 'normalized';

/**
 * El A/B de un archivo normalizado: el original y el resultado, con un conmutador que mantiene la posición. Al cambiar
 * de versión, el medio se queda donde estaba: se guarda el tiempo antes de cambiar la fuente y se vuelve a él cuando
 * la nueva carga sus metadatos.
 *
 * @author Pablo Contreras
 * @since 2026/11/22
 */
export function NormalizeListen({ job }: { job: Job }): React.JSX.Element {
  const api = useApi();
  const input = (job.params as { input: string }).input;
  const [version, setVersion] = useState<Version>('original');
  const [media, setMedia] = useState<HTMLMediaElement | null>(null);
  const { playing, toggle } = useSyncedMedia(media);
  const resumeAt = useRef<number | null>(null);

  const video = isVideoPath(input);
  const normalized = `${job.output_dir ?? ''}/normalized.${baseName(input).split('.').pop() ?? ''}`;
  const src = version === 'original' ? api.fileUrl(input) : api.fileUrl(normalized);

  useEffect(() => {
    if (!media) return;
    const onLoad = () => {
      if (resumeAt.current !== null) media.currentTime = resumeAt.current;
      resumeAt.current = null;
    };
    media.addEventListener('loadedmetadata', onLoad);
    return () => media.removeEventListener('loadedmetadata', onLoad);
  }, [media]);

  const switchTo = (next: Version) => {
    resumeAt.current = media?.currentTime ?? null;
    setVersion(next);
  };

  return (
    <UIStack gap="sm">
      <UIText variant="subtitle">{baseName(input)}</UIText>
      <UIStack direction="row" gap="xs" align="center">
        <UIButton variant={version === 'original' ? 'primary' : 'secondary'} aria-pressed={version === 'original'} onClick={() => switchTo('original')}>
          {t('normalize.ab.original')}
        </UIButton>
        <UIButton variant={version === 'normalized' ? 'primary' : 'secondary'} aria-pressed={version === 'normalized'} onClick={() => switchTo('normalized')}>
          {t('normalize.ab.normalized')}
        </UIButton>
        <UIIconButton
          icon={playing ? 'pause' : 'play'}
          label={playing ? t('media.action.pause') : t('media.action.play')}
          onClick={toggle}
        />
      </UIStack>
      <UIMedia kind={video ? 'video' : 'audio'} src={src} mediaRef={setMedia} />
    </UIStack>
  );
}

import { useState } from 'react';

import { open } from '@tauri-apps/plugin-dialog';

import { UIButton } from '@/shared/components/atoms/UIButton';
import { UIStack } from '@/shared/components/atoms/UIStack';
import { UIText } from '@/shared/components/atoms/UIText';
import { t } from '@/shared/i18n/t';

const EXTENSIONS = ['wav', 'mp3', 'm4a', 'flac', 'ogg', 'aac', 'mp4', 'mov', 'mkv', 'webm', 'avi', 'm4v'];

/** Muestra una fuente ausente y permite reasignar su ruta desde el diálogo nativo. */
export function ClipMissing({
  src,
  onRelink,
}: {
  src: string;
  onRelink: (oldSource: string, newSource: string) => void;
}): React.JSX.Element {
  const [failed, setFailed] = useState(false);

  async function find(): Promise<void> {
    setFailed(false);
    try {
      const picked = await open({ multiple: false, filters: [{ name: t('media.files.filter'), extensions: EXTENSIONS }] });
      if (typeof picked === 'string') onRelink(src, picked);
    } catch {
      setFailed(true);
    }
  }

  return (
    <UIStack role="alert" direction="row" align="center" gap="sm">
      <UIText variant="caption">{t('editor.clip.missing', { source: src })}</UIText>
      <UIButton variant="secondary" icon="import-file" onClick={() => void find()}>
        {t('editor.clip.find')}
      </UIButton>
      {failed ? <UIText variant="caption">{t('editor.clip.relink_error')}</UIText> : null}
    </UIStack>
  );
}

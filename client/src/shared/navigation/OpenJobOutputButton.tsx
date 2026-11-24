import { useState } from 'react';

import { useApi } from '@/shared/api/context';
import { UIIconButton } from '@/shared/components/molecules/UIIconButton';
import { toast } from '@/shared/components/molecules/UIToast';
import { t } from '@/shared/i18n/t';

import { openInEditor } from './sendTo';

interface Props {
  outputDir: string | null | undefined;
}

interface MediaEntry {
  path: string;
  kind: string;
}

/** Busca los medios de una salida de trabajo y los agrega al Editor. */
export function OpenJobOutputButton({ outputDir }: Props): React.JSX.Element {
  const api = useApi();
  const [busy, setBusy] = useState(false);

  async function openOutput(): Promise<void> {
    if (!outputDir || busy) return;
    setBusy(true);
    try {
      const query = new URLSearchParams({ path: outputDir, kinds: 'audio,video' });
      const result = await api.get<{ entries: MediaEntry[] }>(`/fs/list?${query}`);
      const paths = result.entries
        .filter((entry) => entry.kind === 'audio' || entry.kind === 'video')
        .map((entry) => entry.path);
      if (paths.length > 0) openInEditor(paths);
    } catch {
      toast.error(t('editor.import.error'));
    } finally {
      setBusy(false);
    }
  }

  return (
    <UIIconButton
      icon="editor"
      label={t('action.open_editor')}
      disabled={!outputDir || busy}
      onClick={() => void openOutput()}
    />
  );
}

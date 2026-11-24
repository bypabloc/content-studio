import { UIIconButton } from '@/shared/components/molecules/UIIconButton';
import { t } from '@/shared/i18n/t';

import { openInEditor } from './sendTo';

export function OpenInEditorButton({ paths }: { paths: string[] }): React.JSX.Element {
  const available = paths.filter(Boolean);
  return (
    <UIIconButton
      icon="editor"
      label={t('action.open_editor')}
      disabled={available.length === 0}
      onClick={() => openInEditor(available)}
    />
  );
}

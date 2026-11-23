import { UIButton } from '@/shared/components/atoms/UIButton';
import { UIStack } from '@/shared/components/atoms/UIStack';
import { t } from '@/shared/i18n/t';

export type BrowserRoot = { name: string; path: string };

/** Raíces del sistema y carpetas favoritas del explorador del editor. */
export function FolderTree({
  roots,
  currentPath,
  onSelect,
}: {
  roots: BrowserRoot[];
  currentPath: string;
  onSelect: (path: string) => void;
}): React.JSX.Element {
  return (
    <UIStack role="tree" aria-label={t('editor.browser.tree')} gap="xs">
      {roots.map((root) => (
        <UIButton
          key={root.path}
          role="treeitem"
          variant={root.path === currentPath ? 'secondary' : 'ghost'}
          aria-current={root.path === currentPath ? 'location' : undefined}
          icon="open-folder"
          block
          onClick={() => onSelect(root.path)}
        >
          {root.name}
        </UIButton>
      ))}
    </UIStack>
  );
}

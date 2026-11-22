import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { FolderTree } from '@/features/editor/browser/FolderTree';
import { t } from '@/shared/i18n/t';

afterEach(cleanup);

describe('FolderTree', () => {
  it('muestra las raíces y abre la carpeta seleccionada', () => {
    const onSelect = vi.fn();
    render(
      <FolderTree
        roots={[
          { name: 'home', path: 'D:\\Users\\Pablo' },
          { name: 'Music', path: 'D:\\Users\\Pablo\\Music' },
        ]}
        currentPath="D:\\Users\\Pablo"
        onSelect={onSelect}
      />,
    );

    fireEvent.click(screen.getByRole('treeitem', { name: 'Music' }));

    expect(screen.getByRole('tree', { name: t('editor.browser.tree') })).toBeTruthy();
    expect(onSelect).toHaveBeenCalledWith('D:\\Users\\Pablo\\Music');
  });
});

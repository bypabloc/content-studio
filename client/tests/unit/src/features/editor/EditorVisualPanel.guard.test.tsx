import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { EditorVisualPanel } from '@/features/editor/EditorVisualPanel';
import type { Doc, Keyframe } from '@/features/editor/model/types';
import type { VisualProperty } from '@/features/editor/model/visual';

const mocks = vi.hoisted(() => ({ createCompositor: vi.fn(() => ({ render: vi.fn(), destroy: vi.fn() })) }));
vi.mock('@/shared/api/context', () => ({ useApi: () => ({ queryUrl: vi.fn(() => '/media') }) }));
vi.mock('@/features/editor/preview/webgl', () => ({ createCompositor: mocks.createCompositor }));
vi.mock('@/features/editor/preview/useLayerSources', () => ({ useLayerSources: () => ({ get: vi.fn() }) }));
vi.mock('@/features/editor/Inspector', () => ({
  Inspector: ({
    onChange,
    onToggleKeyframe,
    onEaseChange,
    onCanvasChange,
  }: {
    onChange: (property: VisualProperty, value: number) => void;
    onToggleKeyframe: (property: VisualProperty) => void;
    onEaseChange: (property: VisualProperty, ease: Keyframe['ease']) => void;
    onCanvasChange: (change: Partial<Doc['canvas']>) => void;
  }) => (
    <button
      aria-label="invoke-stale-inspector-actions"
      onClick={() => {
        onChange('x', 10);
        onToggleKeyframe('x');
        onEaseChange('x', 'hold');
        onCanvasChange({ width: 2048 });
      }}
    />
  ),
}));

afterEach(cleanup);

const doc: Doc = {
  version: 2,
  name: 'demo',
  sample_rate: 48000,
  canvas: { width: 1280, height: 720, fps: 30, background: '#000000' },
  tracks: [],
  clips: [],
  markers: [],
  transitions: [],
};

describe('EditorVisualPanel: selección que cambia durante una acción', () => {
  it('ignora cambios visuales obsoletos y conserva los ajustes del lienzo', () => {
    const onPreviewDoc = vi.fn();
    const onCommitPreview = vi.fn();
    render(
      <EditorVisualPanel
        doc={doc}
        path="/project.json"
        time={0}
        selectedIds={[]}
        onPreviewDoc={onPreviewDoc}
        onCommitPreview={onCommitPreview}
        onCancelPreview={vi.fn()}
        onSeek={vi.fn()}
        onAddTransition={vi.fn()}
        onAddText={vi.fn()}
      />,
    );

    fireEvent.click(screen.getByRole('button', { name: 'invoke-stale-inspector-actions' }));

    expect(onPreviewDoc).toHaveBeenCalledOnce();
    expect((onPreviewDoc.mock.calls[0][0] as Doc).canvas.width).toBe(2048);
    expect(onCommitPreview).toHaveBeenCalledOnce();
  });
});

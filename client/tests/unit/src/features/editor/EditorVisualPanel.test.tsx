import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { EditorVisualPanel } from '@/features/editor/EditorVisualPanel';
import type { Clip, Doc, VisualClip } from '@/features/editor/model/types';
import { t } from '@/shared/i18n/t';

const mocks = vi.hoisted(() => ({
  createCompositor: vi.fn(() => ({ render: vi.fn(), destroy: vi.fn() })),
  sources: { get: vi.fn() },
}));
vi.mock('@/shared/api/context', () => ({ useApi: () => ({ queryUrl: vi.fn(() => '/media') }) }));
vi.mock('@/features/editor/preview/webgl', () => ({ createCompositor: mocks.createCompositor }));
vi.mock('@/features/editor/preview/useLayerSources', () => ({ useLayerSources: () => mocks.sources }));

afterEach(cleanup);

const visual: VisualClip = {
  id: 'logo', track: 'video', src: 'logo.png', src_in: 0, src_out: 4, start: 0, fade_in: 0, fade_out: 0, media: 'image',
  transform: {
    x: 0, y: 0, scale_x: 1, scale_y: 1, rotation: 0, opacity: 1,
    crop: { l: 0, t: 0, r: 0, b: 0 }, anchor_x: 0.5, anchor_y: 0.5,
  },
  keyframes: {},
};
const doc: Doc = {
  version: 2, name: 'demo', sample_rate: 48000,
  canvas: { width: 1280, height: 720, fps: 30, background: '#000000' },
  tracks: [{ id: 'video', kind: 'video', name: 'Video', opacity: 1, hidden: false, locked: false }],
  clips: [visual], markers: [], transitions: [],
};

describe('EditorVisualPanel', () => {
  it('registra los cambios del inspector como un paso del historial', () => {
    const onPreviewDoc = vi.fn();
    const onCommitPreview = vi.fn();
    render(
      <EditorVisualPanel
        doc={doc}
        path="/project.json"
        time={1}
        selectedIds={['logo']}
        onPreviewDoc={onPreviewDoc}
        onCommitPreview={onCommitPreview}
        onCancelPreview={vi.fn()}
        onSeek={vi.fn()}
        onAddTransition={vi.fn()}
      />,
    );

    fireEvent.change(screen.getByLabelText(t('editor.inspector.property_x')), { target: { value: '160' } });

    const edited = onPreviewDoc.mock.calls[0][0] as Doc;
    expect((edited.clips[0] as VisualClip).transform.x).toBe(160);
    expect(onCommitPreview).toHaveBeenCalledOnce();
  });

  it('confirma keyframes y cambios del lienzo y reenvía las transiciones', async () => {
    const onPreviewDoc = vi.fn();
    const onCommitPreview = vi.fn();
    const onAddTransition = vi.fn();
    const animated = structuredClone(doc);
    (animated.clips[0] as VisualClip).keyframes.x = [{ t: 1, value: 30, ease: 'linear' }];
    render(
      <EditorVisualPanel
        doc={animated}
        path="/project.json"
        time={1}
        selectedIds={['logo']}
        onPreviewDoc={onPreviewDoc}
        onCommitPreview={onCommitPreview}
        onCancelPreview={vi.fn()}
        onSeek={vi.fn()}
        onAddTransition={onAddTransition}
      />,
    );

    fireEvent.click(screen.getByRole('button', {
      name: t('editor.inspector.keyframe', { property: t('editor.inspector.property_x') }),
    }));
    const easeLabel = t('editor.inspector.ease', { property: t('editor.inspector.property_x') });
    await userEvent.click(await screen.findByRole('combobox', { name: easeLabel }));
    await userEvent.click(await screen.findByRole('option', { name: t('editor.inspector.ease_hold') }));

    fireEvent.change(screen.getByLabelText(t('editor.inspector.canvas_width')), { target: { value: '2048' } });
    const latest = onPreviewDoc.mock.calls[onPreviewDoc.mock.calls.length - 1];
    if (!latest) throw new Error('El inspector no emitió el cambio del lienzo');
    expect((latest[0] as Doc).canvas.width).toBe(2048);
    expect(onCommitPreview).toHaveBeenCalledTimes(3);

    fireEvent.click(screen.getByRole('button', { name: t('editor.transitions.fade') }));
    expect(onAddTransition).toHaveBeenCalledWith('fade');
  });

  it('deja sin inspector visual una selección que no existe en el documento', () => {
    render(
      <EditorVisualPanel
        doc={doc}
        path="/project.json"
        time={0}
        selectedIds={['missing']}
        onPreviewDoc={vi.fn()}
        onCommitPreview={vi.fn()}
        onCancelPreview={vi.fn()}
        onSeek={vi.fn()}
        onAddTransition={vi.fn()}
      />,
    );
    expect(screen.getByText(t('editor.inspector.no_selection'))).toBeTruthy();
  });

  it('no trata como visual un clip de audio seleccionado', () => {
    const audioDoc = structuredClone(doc);
    const audio: Clip = { id: 'voice', track: 'audio', src: 'voice.wav', src_in: 0, src_out: 4, start: 0, gain_db: 0, fade_in: 0, fade_out: 0 };
    audioDoc.clips = [audio];
    render(
      <EditorVisualPanel
        doc={audioDoc}
        path="/project.json"
        time={0}
        selectedIds={['voice']}
        onPreviewDoc={vi.fn()}
        onCommitPreview={vi.fn()}
        onCancelPreview={vi.fn()}
        onSeek={vi.fn()}
        onAddTransition={vi.fn()}
      />,
    );
    expect(screen.getByText(t('editor.inspector.no_selection'))).toBeTruthy();
  });
});

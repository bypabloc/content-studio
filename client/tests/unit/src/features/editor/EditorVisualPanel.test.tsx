import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { EditorVisualPanel } from '@/features/editor/EditorVisualPanel';
import type { BlendMode, ChromaKey, Clip, ColorEffects, Doc, TextClip, VideoClip, VisualClip } from '@/features/editor/model/types';
import { t } from '@/shared/i18n/t';

const mocks = vi.hoisted(() => ({
  createCompositor: vi.fn(() => ({ render: vi.fn(), destroy: vi.fn() })),
  sources: { get: vi.fn() },
}));
vi.mock('@/shared/api/context', () => ({ useApi: () => ({ queryUrl: vi.fn(() => '/media') }) }));
vi.mock('@/features/editor/preview/webgl', () => ({ createCompositor: mocks.createCompositor }));
vi.mock('@/features/editor/preview/useLayerSources', () => ({ useLayerSources: () => mocks.sources }));
vi.mock('@/features/editor/TextInspector', () => ({
  TextInspector: ({
    clip, onChange, onRasterChange,
  }: {
    clip: TextClip | null;
    onChange: (id: string, style: TextClip['text']) => void;
    onRasterChange: (id: string, src: string) => void;
  }) => {
    if (!clip) return null;
    return (
      <>
        <button type="button" onClick={() => {
          onChange('missing', clip.text);
          onChange(clip.id, { ...clip.text, content: 'Actualizado' });
        }}>change-text</button>
        <button type="button" onClick={() => {
          onRasterChange('missing', 'media/pending.png');
          onRasterChange(clip.id, 'media/text-title-hash.png');
        }}>change-raster</button>
      </>
    );
  },
}));
vi.mock('@/features/editor/ColorInspector', () => ({
  ColorInspector: ({
    clip, onChange,
  }: { clip: VisualClip | null; onChange: (id: string, color: ColorEffects) => void }) => {
    if (!clip) return null;
    return <button type="button" onClick={() => {
      const color = { brightness: 0.25, contrast: 1, saturation: 1, gamma: 1 };
      onChange('missing', color);
      onChange(clip.id, color);
    }}>change-color</button>;
  },
}));
vi.mock('@/features/editor/EffectsInspector', () => ({
  EffectsInspector: ({
    clip, onChange,
  }: {
    clip: VisualClip | null;
    onChange: (id: string, change: { blend_mode?: BlendMode; chroma?: ChromaKey | null }) => void;
  }) => {
    if (!clip) return null;
    return <button type="button" onClick={() => {
      onChange('missing', { blend_mode: 'screen' });
      onChange(clip.id, { blend_mode: 'multiply' });
      onChange(clip.id, { chroma: { color: '#00ff00', similarity: 0.2, blend: 0.1 } });
      onChange(clip.id, { chroma: null });
    }}>change-effects</button>;
  },
}));

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
  it('aplica color y efectos solo al clip visual seleccionado', () => {
    const onPreviewDoc = vi.fn();
    const onCommitPreview = vi.fn();
    render(
      <EditorVisualPanel
        doc={doc} path="/project.json" time={0} selectedIds={['logo']}
        onPreviewDoc={onPreviewDoc} onCommitPreview={onCommitPreview} onCancelPreview={vi.fn()}
        onSeek={vi.fn()} onAddTransition={vi.fn()} onAddText={vi.fn()}
      />,
    );

    fireEvent.click(screen.getByRole('button', { name: 'change-color' }));
    expect((onPreviewDoc.mock.calls[0][0] as Doc).clips[0]).toMatchObject({ color: { brightness: 0.25 } });
    fireEvent.click(screen.getByRole('button', { name: 'change-effects' }));
    expect((onPreviewDoc.mock.calls[1][0] as Doc).clips[0]).toMatchObject({ blend_mode: 'multiply' });
    expect((onPreviewDoc.mock.calls[2][0] as Doc).clips[0]).toMatchObject({ chroma: { color: '#00ff00' } });
    expect((onPreviewDoc.mock.calls[3][0] as Doc).clips[0]).not.toHaveProperty('chroma');
    expect(onCommitPreview).toHaveBeenCalledTimes(4);
  });

  it('permite editar transformaciones de un título seleccionado', () => {
    const title = {
      ...visual, id: 'title', src: 'media/text-title-hash.png', media: 'text', raster: 'media/text-title-hash.png',
      text: {
        content: 'Hola', font: 'Arial', weight: 700, size: 48, color: '#ffffff',
        stroke: { width: 2, color: '#000000' }, shadow: { x: 0, y: 2, blur: 4, color: '#000000' },
        align: 'center', line_height: 1.2, max_width: 800,
      },
    } as TextClip;
    const titleDoc = { ...doc, version: 3, clips: [title] } as Doc;
    const onPreviewDoc = vi.fn();
    render(
      <EditorVisualPanel
        doc={titleDoc} path="/project.json" time={1} selectedIds={['title']}
        onPreviewDoc={onPreviewDoc} onCommitPreview={vi.fn()} onCancelPreview={vi.fn()}
        onSeek={vi.fn()} onAddTransition={vi.fn()} onAddText={vi.fn()}
      />,
    );

    fireEvent.change(screen.getByLabelText(t('editor.inspector.property_x')), { target: { value: '120' } });

    expect((onPreviewDoc.mock.calls[0][0].clips[0] as TextClip).transform.x).toBe(120);
  });

  it('confirma cambios del texto y del raster del clip seleccionado', () => {
    const title: TextClip = {
      ...visual, id: 'title', src: 'media/text-title-hash.png', media: 'text', raster: 'media/text-title-hash.png',
      text: {
        content: 'Hola', font: 'Arial', weight: 700, size: 48, color: '#ffffff',
        stroke: { width: 2, color: '#000000' }, shadow: { x: 0, y: 2, blur: 4, color: '#000000' },
        align: 'center', line_height: 1.2, max_width: 800,
      },
    };
    const titleDoc: Doc = { ...doc, version: 3, clips: [title] };
    const onPreviewDoc = vi.fn();
    const onCommitPreview = vi.fn();
    render(
      <EditorVisualPanel
        doc={titleDoc} path="/project.json" time={1} selectedIds={['title']}
        onPreviewDoc={onPreviewDoc} onCommitPreview={onCommitPreview} onCancelPreview={vi.fn()}
        onSeek={vi.fn()} onAddTransition={vi.fn()} onAddText={vi.fn()}
      />,
    );

    fireEvent.click(screen.getByRole('button', { name: 'change-text' }));
    expect((onPreviewDoc.mock.calls[0][0] as Doc).clips[0]).toMatchObject({ text: { content: 'Actualizado' } });
    fireEvent.click(screen.getByRole('button', { name: 'change-raster' }));
    expect((onPreviewDoc.mock.calls[1][0] as Doc).clips[0]).toMatchObject({
      src: 'media/text-title-hash.png', raster: 'media/text-title-hash.png',
    });
    expect(onCommitPreview).toHaveBeenCalledTimes(2);
  });

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
        onAddText={vi.fn()}
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
        onAddText={vi.fn()}
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
        onAddText={vi.fn()}
      />,
    );
    expect(screen.getByText(t('editor.inspector.no_selection'))).toBeTruthy();
  });

  it('permite cambiar la velocidad de un clip de audio seleccionado', () => {
    const audioDoc = structuredClone(doc);
    const audio: Clip = { id: 'voice', track: 'audio', src: 'voice.wav', src_in: 0, src_out: 4, start: 0, gain_db: 0, fade_in: 0, fade_out: 0 };
    audioDoc.clips = [audio];
    const onPreviewDoc = vi.fn();
    const onCommitPreview = vi.fn();
    render(
      <EditorVisualPanel
        doc={audioDoc}
        path="/project.json"
        time={0}
        selectedIds={['voice']}
        onPreviewDoc={onPreviewDoc}
        onCommitPreview={onCommitPreview}
        onCancelPreview={vi.fn()}
        onSeek={vi.fn()}
        onAddTransition={vi.fn()}
        onAddText={vi.fn()}
      />,
    );

    fireEvent.change(screen.getByLabelText(t('editor.inspector.speed')), { target: { value: '0.5' } });

    expect((onPreviewDoc.mock.calls[0][0] as Doc).clips[0].speed).toBe(0.5);
    expect(onCommitPreview).toHaveBeenCalledOnce();
  });

  it('sincroniza la velocidad del audio y el video enlazados', () => {
    const video: VideoClip = { ...visual, id: 'video', media: 'video', speed: 1, link: 'source-pair' };
    const audio: Clip = {
      id: 'audio', track: 'audio', src: 'source.mp4', src_in: 0, src_out: 4, start: 0,
      gain_db: 0, fade_in: 0, fade_out: 0, speed: 1, link: 'source-pair',
    };
    const linkedDoc: Doc = {
      ...doc,
      version: 3,
      tracks: [
        ...doc.tracks,
        { id: 'audio', kind: 'audio', name: 'Audio', volume_db: 0, mute: false, solo: false, locked: false, height: 80 },
      ],
      clips: [video, audio],
    };
    const onPreviewDoc = vi.fn();
    render(
      <EditorVisualPanel
        doc={linkedDoc} path="/project.json" time={0} selectedIds={['video']}
        onPreviewDoc={onPreviewDoc} onCommitPreview={vi.fn()} onCancelPreview={vi.fn()}
        onSeek={vi.fn()} onAddTransition={vi.fn()} onAddText={vi.fn()}
      />,
    );

    fireEvent.change(screen.getByLabelText(t('editor.inspector.speed')), { target: { value: '2' } });

    expect((onPreviewDoc.mock.calls[0][0] as Doc).clips.map((clip) => clip.speed)).toEqual([2, 2]);
  });
});

import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { EditorWorkspace } from '@/features/editor/EditorWorkspace';
import type { Doc, TextClip, VideoClip } from '@/features/editor/model/types';
import type { TextPresetName } from '@/features/editor/text/presets';
import { t } from '@/shared/i18n/t';

const { api, open, playback, recorder, importedPaths } = vi.hoisted(() => ({
  api: { get: vi.fn(), put: vi.fn(), upload: vi.fn(), queryUrl: vi.fn((path: string) => path), fileUrl: vi.fn() },
  open: vi.fn(),
  playback: { position: 2, playing: false, seek: vi.fn(), setPlaying: vi.fn(), stop: vi.fn() },
  recorder: { recording: false, uploading: false, levels: { rms: -96, peak: -96 }, latencyMs: 0, error: null, start: vi.fn(), stop: vi.fn() },
  importedPaths: [] as string[],
}));
vi.mock('@/shared/api/context', () => ({ useApi: () => api }));
vi.mock('@/features/editor/playback/usePlayback', () => ({ usePlayback: () => playback }));
vi.mock('@/features/editor/useTrackRecorder', () => ({ useTrackRecorder: () => recorder }));
vi.mock('@/features/editor/useNativeDrop', () => ({
  useNativeDrop: (onPaths: (paths: string[]) => void) => ({ dragging: false, pick: async () => onPaths(importedPaths) }),
}));
vi.mock('@/features/recording/MicrophonePicker', () => ({
  MicrophonePicker: ({ onChange }: { onChange: (value: string) => void }) => (
    <button aria-label="test-microphone" onClick={() => onChange('device-2')} />
  ),
}));
vi.mock('@tauri-apps/plugin-dialog', () => ({ open }));
vi.mock('@/features/editor/TextInspector', () => ({
  TextInspector: ({ onAdd }: { onAdd: (preset: TextPresetName) => void }) => (
    <div>
      <button type="button" onClick={() => onAdd('lower-third')}>add-text-lower-third</button>
      <button type="button" onClick={() => onAdd('title-center')}>add-text-title-center</button>
      <button type="button" onClick={() => onAdd('caption-bold')}>add-text-caption-bold</button>
    </div>
  ),
}));

const PATH = 'D:/out/editor/demo/project.json';
const DOC: Doc = {
  version: 2,
  name: 'demo',
  sample_rate: 48000,
  canvas: { width: 1920, height: 1080, fps: 30, background: '#000000' },
  tracks: [{ id: 'voice', kind: 'audio', name: 'Voz', volume_db: 0, mute: false, solo: false, locked: false, height: 80 }],
  clips: [{ id: 'clip-1', track: 'voice', src: 'missing.wav', src_in: 0, src_out: 4, start: 0, gain_db: 0, fade_in: 0, fade_out: 0 }],
  markers: [],
  transitions: [],
};
const project = { path: PATH, hash: 'hash-1', doc: DOC, missing: ['missing.wav'] };

function videoClip(id: string, start: number): VideoClip {
  return {
    id, track: 'video', src: `${id}.mp4`, media: 'video', src_in: 0, src_out: 2, start, fade_in: 0, fade_out: 0,
    speed: 1, transform: {
      x: 0, y: 0, scale_x: 1, scale_y: 1, rotation: 0, opacity: 1,
      crop: { l: 0, t: 0, r: 0, b: 0 }, anchor_x: 0.5, anchor_y: 0.5,
    }, keyframes: {}, color: { brightness: 0, contrast: 1, saturation: 1, gamma: 1 }, blend_mode: 'normal',
  };
}

function version3Project(videoTrack = false): typeof project {
  const doc = structuredClone(DOC);
  doc.version = 3;
  doc.clips = doc.clips.map((clip) => ({ ...clip, speed: 1 }));
  if (videoTrack) doc.tracks.push({ id: 'video', kind: 'video', name: 'Video', opacity: 1, hidden: false, locked: false });
  return { ...project, doc, missing: [] };
}

beforeEach(() => {
  importedPaths.splice(0, importedPaths.length, 'D:/Music/song.wav');
  playback.position = 2;
  playback.playing = false;
  api.get.mockImplementation((url: string) => {
    if (url === '/fs/roots') return Promise.resolve({ roots: [{ name: 'Music', path: 'D:/Music' }] });
    if (url === '/settings/editor.favorites') return Promise.resolve({ value: [] });
    if (url.includes('/settings/')) return Promise.resolve({ value: null });
    if (url.startsWith('/fs/list?')) return Promise.resolve({ path: 'D:/Music', entries: [] });
    if (url.startsWith('/fs/info?')) return Promise.resolve({ duration: 3, kind: 'audio', has_audio: true });
    return Promise.reject(new Error('unknown endpoint'));
  });
  api.put.mockResolvedValue({ hash: 'hash-2' });
  open.mockResolvedValue('D:/Music/song.wav');
  recorder.recording = false;
  recorder.uploading = false;
  recorder.error = null;
  recorder.start.mockReset();
  recorder.stop.mockReset();
});

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe('EditorWorkspace', () => {
  it('importa medios en una pista nueva, divide en el cabezal y renombra y borra marcadores', async () => {
    render(<EditorWorkspace project={project} onBack={vi.fn()} />);
    const workspace = screen.getByRole('region', { name: t('editor.project.workspace', { name: 'demo' }) });

    fireEvent.keyDown(workspace, { key: 's' });
    await waitFor(() => expect(screen.getAllByRole('button', { name: /missing\.wav/ })).toHaveLength(2));
    fireEvent.keyDown(workspace, { key: 'm' });
    const marker = await screen.findByRole('button', { name: t('editor.marker.default_name', { n: 1 }) });
    fireEvent.doubleClick(marker);
    const name = screen.getByRole('textbox', { name: t('editor.marker.rename') });
    fireEvent.change(name, { target: { value: 'Fin' } });
    fireEvent.keyDown(name, { key: 'Enter' });
    const renamed = await screen.findByRole('button', { name: 'Fin' });
    fireEvent.click(renamed);
    fireEvent.keyDown(workspace, { key: 'Delete' });
    await waitFor(() => expect(screen.queryByRole('button', { name: 'Fin' })).toBeNull());

    fireEvent.click(screen.getByRole('button', { name: t('action.import') }));
    await waitFor(() => expect(api.get).toHaveBeenCalledWith('/fs/info?path=D%3A%2FMusic%2Fsong.wav'));
    expect(await screen.findByRole('group', { name: t('editor.timeline.lane', { name: t('editor.track.new_name', { n: 2 }) }) })).toBeTruthy();
  });

  it('importa imágenes y videos en pistas visuales y enlaza el audio del video', async () => {
    importedPaths.splice(0, importedPaths.length, 'D:/Media/logo.png', 'D:/Media/scene.mp4');
    api.get.mockImplementation((url: string) => {
      if (url === '/fs/roots') return Promise.resolve({ roots: [{ name: 'Media', path: 'D:/Media' }] });
      if (url === '/settings/editor.favorites') return Promise.resolve({ value: [] });
      if (url.includes('/settings/')) return Promise.resolve({ value: null });
      if (url.startsWith('/fs/list?')) return Promise.resolve({ path: 'D:/Media', entries: [] });
      if (url.includes('logo.png')) return Promise.resolve({ duration: 5, kind: 'image', has_audio: false });
      if (url.includes('scene.mp4')) return Promise.resolve({ duration: 3, kind: 'video', has_audio: true });
      return Promise.reject(new Error('unknown endpoint'));
    });
    render(<EditorWorkspace project={project} onBack={vi.fn()} />);

    fireEvent.click(screen.getByRole('button', { name: t('action.import') }));
    await waitFor(() => expect(api.put).toHaveBeenCalled());

    const saved = api.put.mock.calls.at(-1)?.[1] as Doc;
    const visualTrack = saved.tracks.find((track) => track.kind === 'video');
    const importedAudioTrack = saved.tracks.find((track) => track.kind === 'audio' && track.id !== 'voice');
    const image = saved.clips.find((clip) => clip.src === 'D:/Media/logo.png');
    const video = saved.clips.find((clip) => clip.src === 'D:/Media/scene.mp4' && clip.media === 'video');
    const linkedAudio = saved.clips.find((clip) => clip.src === 'D:/Media/scene.mp4' && !clip.media);

    expect(visualTrack).toBeTruthy();
    expect(image).toMatchObject({ media: 'image', track: visualTrack?.id, src_in: 0, src_out: 5, start: 2 });
    expect(video).toMatchObject({ media: 'video', track: visualTrack?.id, src_in: 0, src_out: 3, start: 7 });
    expect(linkedAudio).toMatchObject({ track: importedAudioTrack?.id, src_in: 0, src_out: 3, start: 7, gain_db: 0 });
    expect(video?.link).toBeTruthy();
    expect(linkedAudio?.link).toBe(video?.link);
  });

  it('importa las rutas solicitadas en el cabezal y avisa cuando termina', async () => {
    const onAddHandled = vi.fn();
    render(<EditorWorkspace project={project} onBack={vi.fn()} pendingAdd={['D:/Music/song.wav']} onAddHandled={onAddHandled} />);

    await waitFor(() => expect(api.put).toHaveBeenCalled());
    const saved = api.put.mock.calls.at(-1)?.[1] as Doc;

    expect(saved.clips).toEqual(expect.arrayContaining([expect.objectContaining({ src: 'D:/Music/song.wav', start: 2 })]));
    expect(onAddHandled).toHaveBeenCalledTimes(1);
  });

  it('arma la primera pista y comienza a grabar al crear un proyecto desde Inicio', async () => {
    const onAutoRecordComplete = vi.fn();
    render(<EditorWorkspace project={project} onBack={vi.fn()} autoRecord onAutoRecordComplete={onAutoRecordComplete} />);

    await waitFor(() => expect(recorder.start).toHaveBeenCalledOnce());
    expect(screen.getByRole('button', { name: t('editor.track.arm', { name: 'Voz' }) }).getAttribute('aria-pressed')).toBe('true');
    expect(onAutoRecordComplete).toHaveBeenCalledOnce();
  });

  it('maneja selección, borrado con ripple, teclas en campos, transporte y retorno', async () => {
    const onBack = vi.fn();
    render(<EditorWorkspace project={project} onBack={onBack} />);
    const workspace = screen.getByRole('region', { name: t('editor.project.workspace', { name: 'demo' }) });
    fireEvent.click(screen.getByRole('button', { name: /missing\.wav/ }));
    fireEvent.keyDown(workspace, { key: 'Delete', shiftKey: true });
    await waitFor(() => expect(screen.queryByText(t('editor.clip.missing', { source: 'missing.wav' }))).toBeNull());
    fireEvent.click(screen.getByRole('button', { name: t('subtitles.home.back') }));
    expect(onBack).toHaveBeenCalledOnce();

    cleanup();
    const second = render(<EditorWorkspace project={project} onBack={onBack} />);
    const arm = screen.getByRole('button', { name: t('editor.track.arm', { name: 'Voz' }) });
    fireEvent.click(arm);
    expect(arm.getAttribute('aria-pressed')).toBe('true');
    const range = screen.getByRole('slider', { name: t('editor.recorder.offset') });
    fireEvent.keyDown(range, { key: 'r' });
    expect(recorder.start).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole('button', { name: t('voices.record.start') }));
    expect(recorder.start).toHaveBeenCalledOnce();
    recorder.recording = true;
    second.rerender(<EditorWorkspace project={project} onBack={onBack} />);
    fireEvent.click(screen.getByRole('button', { name: t('editor.transport.stop') }));
    expect(playback.stop).toHaveBeenCalled();
    expect(recorder.stop).toHaveBeenCalledOnce();
  });

  it('muestra el error al importar una duración inválida y permite reasignar la fuente ausente', async () => {
    api.get.mockImplementation((url: string) => {
      if (url.startsWith('/fs/info?')) return Promise.resolve({ duration: 0 });
      if (url === '/fs/roots') return Promise.resolve({ roots: [{ name: 'Music', path: 'D:/Music' }] });
      if (url === '/settings/editor.favorites') return Promise.resolve({ value: [] });
      if (url.startsWith('/fs/list?')) return Promise.resolve({ path: 'D:/Music', entries: [] });
      if (url.includes('/settings/')) return Promise.resolve({ value: null });
      return Promise.reject(new Error('unknown endpoint'));
    });
    open.mockResolvedValue('D:/Media/voz.wav');
    const { rerender } = render(<EditorWorkspace project={project} onBack={vi.fn()} />);
    fireEvent.click(await screen.findByRole('button', { name: t('action.import') }));
    expect(await screen.findByText(t('editor.import.error'))).toBeTruthy();

    api.get.mockImplementation((url: string) => {
      if (url === '/fs/roots') return Promise.resolve({ roots: [{ name: 'Music', path: 'D:/Music' }] });
      if (url === '/settings/editor.favorites') return Promise.resolve({ value: [] });
      if (url.startsWith('/fs/list?')) return Promise.resolve({ path: 'D:/Music', entries: [] });
      if (url.includes('/settings/')) return Promise.resolve({ value: null });
      return Promise.reject(new Error('unknown endpoint'));
    });
    rerender(<EditorWorkspace project={project} onBack={vi.fn()} />);
    fireEvent.click(screen.getByRole('button', { name: t('editor.clip.find') }));
    await waitFor(() => expect(screen.queryByText(t('editor.clip.missing', { source: 'missing.wav' }))).toBeNull());
  });

  it('inicia la grabación automática aunque no se proporcione un callback opcional', async () => {
    render(<EditorWorkspace project={project} onBack={vi.fn()} autoRecord />);

    await waitFor(() => expect(recorder.start).toHaveBeenCalledOnce());
  });

  it('guarda micrófono y latencia y envía el transporte al inicio', async () => {
    render(<EditorWorkspace project={project} onBack={vi.fn()} />);
    fireEvent.click(screen.getByRole('button', { name: 'test-microphone' }));
    fireEvent.change(screen.getByRole('slider', { name: t('editor.recorder.offset') }), { target: { value: '35' } });
    fireEvent.click(screen.getByRole('button', { name: t('editor.transport.start') }));

    await waitFor(() => expect(api.put).toHaveBeenCalledWith('/settings/editor.record_offset_ms', { value: 35 }));
    expect(api.put).toHaveBeenCalledWith('/settings/select.recording.microphone', { value: 'device-2' });
    expect(playback.seek).toHaveBeenCalledWith(0);
  });

  it('ignora la tecla de transición si el proyecto no tiene pistas visuales', () => {
    render(<EditorWorkspace project={project} onBack={vi.fn()} />);
    fireEvent.keyDown(screen.getByRole('region', { name: t('editor.project.workspace', { name: 'demo' }) }), { key: 't' });
    expect(api.put).not.toHaveBeenCalledWith(expect.stringContaining('/projects'), expect.anything());
  });

  it('agrega texto en un proyecto de solo audio y crea una pista visual con efectos neutrales', async () => {
    render(<EditorWorkspace project={version3Project()} onBack={vi.fn()} />);

    fireEvent.click(screen.getByRole('button', { name: 'add-text-lower-third' }));
    await waitFor(() => expect(api.put).toHaveBeenCalled());

    const saved = api.put.mock.calls.at(-1)?.[1] as Doc;
    const track = saved.tracks.find((item) => item.kind === 'video');
    const title = saved.clips.find((clip): clip is TextClip => 'media' in clip && clip.media === 'text');
    expect(track).toMatchObject({ kind: 'video', name: t('editor.text.track_name'), locked: false });
    expect(title).toMatchObject({
      media: 'text', track: track?.id, start: 2, speed: 1, blend_mode: 'normal',
      color: { brightness: 0, contrast: 1, saturation: 1, gamma: 1 },
    });
    expect(title?.transform.y).toBe(324);
  });

  it.each([
    ['title-center', 0],
    ['caption-bold', 367.2],
  ] as const)('reutiliza la pista visual para el preset %s', async (preset, y) => {
    render(<EditorWorkspace project={version3Project(true)} onBack={vi.fn()} />);

    fireEvent.click(screen.getByRole('button', { name: `add-text-${preset}` }));
    await waitFor(() => expect(api.put).toHaveBeenCalled());

    const saved = api.put.mock.calls.at(-1)?.[1] as Doc;
    const title = saved.clips.find((clip): clip is TextClip => 'media' in clip && clip.media === 'text');
    expect(saved.tracks.filter((track) => track.kind === 'video')).toHaveLength(1);
    expect(title?.transform.y).toBeCloseTo(y);
  });

  it('agrega una transición al corte visual bajo el cabezal', async () => {
    const transitionProject = version3Project(true);
    transitionProject.doc.clips = [videoClip('first', 0), videoClip('second', 2)];
    render(<EditorWorkspace project={transitionProject} onBack={vi.fn()} />);
    const workspace = screen.getByRole('region', { name: t('editor.project.workspace', { name: 'demo' }) });

    fireEvent.keyDown(workspace, { key: 't' });
    await waitFor(() => expect(api.put).toHaveBeenCalled());

    const saved = api.put.mock.calls.at(-1)?.[1] as Doc;
    expect(saved.transitions).toHaveLength(1);
    expect(saved.transitions[0]).toMatchObject({ track: 'video', a: 'first', b: 'second', type: 'fade', duration: 0.5 });
  });
});

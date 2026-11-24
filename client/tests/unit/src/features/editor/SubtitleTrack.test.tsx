import { act, cleanup, render, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { SubtitleTrack } from '@/features/editor/SubtitleTrack';

const mocks = vi.hoisted(() => ({
  api: { get: vi.fn() },
  constructed: vi.fn(),
  manualRender: vi.fn(),
  ready: vi.fn(() => Promise.resolve()),
  destroy: vi.fn(() => Promise.resolve()),
}));

vi.mock('@/shared/api/context', () => ({ useApi: () => mocks.api }));
vi.mock('jassub', () => ({
  default: class FakeJassub {
    ready = mocks.ready();
    manualRender = mocks.manualRender;
    constructor(options: unknown) {
      mocks.constructed(options);
    }
    destroy() {
      return mocks.destroy();
    }
  },
}));

const track = {
  id: 'subs',
  kind: 'subtitles' as const,
  name: 'Subtítulos',
  subtitles_project: '7',
  locked: false,
};

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
  mocks.ready.mockReset().mockResolvedValue(undefined);
});

describe('SubtitleTrack', () => {
  it('renderiza ASS en canvas con el tiempo actual del cabezal y libera JASSUB', async () => {
    mocks.api.get.mockResolvedValue({
      version: 1,
      style: {},
      cues: [{ id: 1, start: 0, end: 2, text: 'hola', words: [{ start: 0, end: 2, text: 'hola' }] }],
    });
    const { container, rerender, unmount } = render(
      <SubtitleTrack track={track} time={1.25} width={1920} height={1080} />,
    );

    await waitFor(() => expect(mocks.manualRender).toHaveBeenCalled());
    expect(mocks.api.get).toHaveBeenCalledWith('/subtitles/7');
    expect(mocks.constructed).toHaveBeenCalledWith(expect.objectContaining({ canvas: container.querySelector('canvas') }));
    expect(mocks.manualRender.mock.calls.at(-1)?.[0]).toEqual(expect.objectContaining({ mediaTime: 1.25 }));

    rerender(<SubtitleTrack track={track} time={1.75} width={1920} height={1080} />);

    await waitFor(() => expect(mocks.manualRender.mock.calls.at(-1)?.[0]).toEqual(expect.objectContaining({ mediaTime: 1.75 })));
    unmount();
    expect(mocks.destroy).toHaveBeenCalledOnce();
  });

  it('aplica el estilo guardado del proyecto al ASS de vista previa', async () => {
    mocks.api.get.mockResolvedValue({
      version: 1,
      style: { size: 62 },
      cues: [{ id: 1, start: 0, end: 2, text: 'hola', words: [{ start: 0, end: 2, text: 'hola' }] }],
    });

    render(<SubtitleTrack track={track} time={1} width={320} height={180} />);

    await waitFor(() => expect(mocks.constructed).toHaveBeenCalled());
    expect(mocks.constructed).toHaveBeenCalledWith(expect.objectContaining({ subContent: expect.stringContaining('Arial,62,') }));
  });

  it('ignora una respuesta que llega después de desmontar la pista', async () => {
    let resolveDocument!: (document: object) => void;
    mocks.api.get.mockReturnValue(new Promise((resolve) => { resolveDocument = resolve; }));
    const { unmount } = render(<SubtitleTrack track={track} time={1} width={320} height={180} />);

    unmount();
    await act(async () => {
      resolveDocument({ version: 1, style: {}, cues: [] });
      await import('jassub');
    });

    expect(mocks.constructed).not.toHaveBeenCalled();
  });

  it('no renderiza cuando JASSUB queda listo después de desmontar', async () => {
    let resolveReady!: () => void;
    mocks.ready.mockImplementation(() => new Promise<void>((resolve) => { resolveReady = resolve; }));
    mocks.api.get.mockResolvedValue({ version: 1, style: {}, cues: [] });
    const { unmount } = render(<SubtitleTrack track={track} time={1} width={320} height={180} />);

    await waitFor(() => expect(mocks.constructed).toHaveBeenCalled());
    unmount();
    await act(async () => resolveReady());

    expect(mocks.manualRender).not.toHaveBeenCalled();
    expect(mocks.destroy).toHaveBeenCalledOnce();
  });

  it('ignora un error al cargar el proyecto de subtítulos', async () => {
    let rejectRequest!: (error: Error) => void;
    mocks.api.get.mockReturnValue(new Promise((_resolve, reject) => { rejectRequest = reject; }));
    render(<SubtitleTrack track={track} time={1} width={320} height={180} />);

    await act(async () => rejectRequest(new Error('offline')));

    expect(mocks.constructed).not.toHaveBeenCalled();
  });
});

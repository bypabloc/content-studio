import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { SubtitlesPreview } from '@/features/subtitles/SubtitlesPreview';
import { t } from '@/shared/i18n/t';

// JASSUB necesita un canvas y un worker: aquí se reemplaza por un objeto con los métodos que usa la vista previa.
const { setTrack, destroy, constructed } = vi.hoisted(() => ({
  setTrack: vi.fn(),
  destroy: vi.fn(() => Promise.resolve()),
  constructed: vi.fn(),
}));
vi.mock('jassub', () => ({
  default: class FakeJassub {
    renderer = { setTrack };
    constructor() {
      constructed();
    }
    destroy() {
      return destroy();
    }
  },
}));

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe('SubtitlesPreview', () => {
  it('dibuja el video y la zona segura de la plataforma elegida', () => {
    const { container } = render(
      <SubtitlesPreview src="file://charla.mp4" ass="" zone="reels" onAspect={() => {}} />,
    );

    expect(container.querySelector('video')).not.toBeNull();
    expect(screen.getByRole('group', { name: t('subtitles.zones.reels') })).toBeTruthy();
  });

  it('sin zona no dibuja ninguna zona segura', () => {
    render(<SubtitlesPreview src="file://charla.mp4" ass="" zone={null} onAspect={() => {}} />);

    expect(screen.queryByRole('group')).toBeNull();
  });

  it('informa la relación de aspecto del video al cargar sus metadatos', () => {
    const onAspect = vi.fn();
    const { container } = render(<SubtitlesPreview src="file://x.mp4" ass="" zone={null} onAspect={onAspect} />);
    const video = container.querySelector('video') as HTMLVideoElement;
    Object.defineProperty(video, 'videoWidth', { value: 1080 });
    Object.defineProperty(video, 'videoHeight', { value: 1920 });

    fireEvent(video, new Event('loadedmetadata'));

    expect(onAspect).toHaveBeenCalledWith(1080 / 1920);
  });

  it('does not report an aspect while the video has no height yet', () => {
    const onAspect = vi.fn();
    const { container } = render(<SubtitlesPreview src="file://x.mp4" ass="" zone={null} onAspect={onAspect} />);
    const video = container.querySelector('video') as HTMLVideoElement;
    Object.defineProperty(video, 'videoHeight', { value: 0 });

    fireEvent(video, new Event('loadedmetadata'));

    expect(onAspect).not.toHaveBeenCalled();
  });

  it('sends a new subtitle track to the renderer when the ASS changes', async () => {
    const { rerender } = render(<SubtitlesPreview src="file://x.mp4" ass="uno" zone={null} onAspect={() => {}} />);
    await waitFor(() => expect(constructed).toHaveBeenCalled());

    rerender(<SubtitlesPreview src="file://x.mp4" ass="dos" zone={null} onAspect={() => {}} />);

    expect(setTrack).toHaveBeenLastCalledWith('dos');
  });
});

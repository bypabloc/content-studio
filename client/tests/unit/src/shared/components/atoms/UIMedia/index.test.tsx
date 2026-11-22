import { cleanup, render } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { UIMedia } from '@/shared/components/atoms/UIMedia';

describe('UIMedia (spec 013, D-6)', () => {
  afterEach(() => {
    cleanup();
  });

  it('un video se muestra como <video> y su elemento se entrega a mediaRef', () => {
    const mediaRef = vi.fn();
    const { container } = render(<UIMedia kind="video" src="file://charla.mp4" mediaRef={mediaRef} />);

    const video = container.querySelector('video');
    expect(video?.getAttribute('src')).toBe('file://charla.mp4');
    expect(mediaRef).toHaveBeenCalledWith(video);
  });

  it('un audio se muestra como <audio> y su elemento se entrega a mediaRef', () => {
    const mediaRef = vi.fn();
    const { container } = render(<UIMedia kind="audio" src="file://voz.wav" mediaRef={mediaRef} />);

    const audio = container.querySelector('audio');
    expect(audio?.getAttribute('src')).toBe('file://voz.wav');
    expect(container.querySelector('video')).toBeNull();
    expect(mediaRef).toHaveBeenCalledWith(audio);
  });
});

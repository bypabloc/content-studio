import { openSection } from './hash';

export type MediaType = 'audio' | 'video';
export type SendDestination = 'convert' | 'normalize' | 'subtitles' | 'mix';

const DESTINATIONS: Record<MediaType, readonly SendDestination[]> = {
  audio: ['convert', 'normalize', 'subtitles', 'mix'],
  video: ['convert', 'subtitles', 'mix'],
};

export function destinationsFor(type: MediaType): readonly SendDestination[] {
  return DESTINATIONS[type];
}

export function sendTo(destination: SendDestination, path: string): void {
  openSection(destination, { path });
}

export function openInEditor(paths: string[]): void {
  const query = new URLSearchParams();
  for (const path of paths.filter(Boolean)) query.append('add', path);
  window.location.hash = `/editor?${query.toString()}`;
}

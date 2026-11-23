import { useCallback, useEffect, useRef, useState } from 'react';

import { duration } from '../model/validate';
import type { AudioClip, Doc } from '../model/types';
import { activeClips, gainAt, gainRamps, positionAt, shouldCorrectDrift, sourceTimeAt } from './scheduler';

type MediaEntry = {
  element: HTMLAudioElement;
  source: MediaElementAudioSourceNode;
  gain: GainNode;
  signature: string;
};

function signature(clip: AudioClip, volume: number): string {
  return [clip.src, clip.src_in, clip.src_out, clip.start, clip.gain_db, clip.fade_in, clip.fade_out, volume].join(':');
}

function scheduleGain(entry: MediaEntry, clip: AudioClip, volume: number, position: number, clock: number): void {
  const track = { volume_db: volume };
  entry.gain.gain.cancelScheduledValues(clock);
  entry.gain.gain.setValueAtTime(gainAt(clip, track, position), clock);
  if (clip.start > position && clip.fade_in === 0) {
    entry.gain.gain.setValueAtTime(10 ** ((clip.gain_db + volume) / 20), clock + clip.start - position);
  }
  for (const [at, value] of gainRamps(clip, track)) {
    if (at > position) entry.gain.gain.linearRampToValueAtTime(value, clock + at - position);
  }
}

function release(entry: MediaEntry): void {
  entry.element.pause();
  entry.source.disconnect();
  entry.gain.disconnect();
}

/** Vista previa sincronizada: un elemento multimedia por clip activo y un GainNode por envolvente. */
export function usePlayback(doc: Doc, fileUrl: (path: string) => string): {
  playing: boolean;
  position: number;
  setPlaying: (playing: boolean) => void;
  seek: (position: number) => void;
  stop: () => void;
} {
  const [playing, setPlayingState] = useState(false);
  const [position, setPositionState] = useState(0);
  const playingRef = useRef(false);
  const positionRef = useRef(0);
  const docRef = useRef(doc);
  const fileUrlRef = useRef(fileUrl);
  const contextRef = useRef<AudioContext | null>(null);
  const mediaRef = useRef(new Map<string, MediaEntry>());
  const anchorRef = useRef({ position: 0, clock: 0 });
  const driftCheckRef = useRef(0);
  const frameRef = useRef<number | null>(null);

  useEffect(() => {
    docRef.current = doc;
    fileUrlRef.current = fileUrl;
  }, [doc, fileUrl]);

  const syncActive = useCallback((time: number, clock: number, checkDrift = true, forceGain = false) => {
    const context = contextRef.current;
    if (!context) return;
    const active = activeClips(docRef.current, time);
    const wanted = new Set(active.map(({ clip }) => clip.id));
    for (const [id, entry] of mediaRef.current) {
      if (wanted.has(id)) continue;
      release(entry);
      mediaRef.current.delete(id);
    }
    for (const { clip, track } of active) {
      const expected = sourceTimeAt(clip, time);
      const nextSignature = signature(clip, track.volume_db);
      let entry = mediaRef.current.get(clip.id);
      if (!entry) {
        const element = new Audio(fileUrlRef.current(clip.src));
        element.preload = 'auto';
        element.currentTime = expected;
        const source = context.createMediaElementSource(element);
        const gain = context.createGain();
        source.connect(gain);
        gain.connect(context.destination);
        entry = { element, source, gain, signature: nextSignature };
        mediaRef.current.set(clip.id, entry);
        scheduleGain(entry, clip, track.volume_db, time, clock);
      } else {
        if (forceGain || entry.signature !== nextSignature) {
          entry.signature = nextSignature;
          scheduleGain(entry, clip, track.volume_db, time, clock);
        }
        if (checkDrift && !entry.element.seeking && shouldCorrectDrift(expected, entry.element.currentTime)) {
          entry.element.currentTime = expected;
        }
      }
      const withinClip = clip.start <= time && time < clip.start + clip.src_out - clip.src_in;
      if (withinClip && entry.element.paused) void entry.element.play().catch(() => undefined);
      else if (!withinClip && !entry.element.paused) entry.element.pause();
    }
  }, []);

  const setPlaying = useCallback((next: boolean) => {
    if (playingRef.current === next) return;
    if (next) {
      if (duration(docRef.current) === 0) return;
      const context = contextRef.current ?? new AudioContext();
      contextRef.current = context;
      void context.resume().catch(() => undefined);
      anchorRef.current = { position: positionRef.current, clock: context.currentTime };
      driftCheckRef.current = context.currentTime;
      playingRef.current = true;
      setPlayingState(true);
      syncActive(positionRef.current, context.currentTime, true, true);
      return;
    }
    playingRef.current = false;
    setPlayingState(false);
    for (const entry of mediaRef.current.values()) entry.element.pause();
  }, [syncActive]);

  const seek = useCallback((requested: number) => {
    const next = Math.min(duration(docRef.current), Math.max(0, requested));
    positionRef.current = next;
    setPositionState(next);
    const context = contextRef.current;
    if (playingRef.current && context) {
      anchorRef.current = { position: next, clock: context.currentTime };
      syncActive(next, context.currentTime, true, true);
    }
  }, [syncActive]);

  const stop = useCallback(() => {
    setPlaying(false);
    seek(0);
  }, [seek, setPlaying]);

  useEffect(() => {
    if (!playing) return;
    const tick = (): void => {
      const context = contextRef.current;
      if (!playingRef.current || !context) return;
      const total = duration(docRef.current);
      const next = positionAt(anchorRef.current.position, anchorRef.current.clock, context.currentTime, total);
      const checkDrift = context.currentTime - driftCheckRef.current >= 0.25;
      if (checkDrift) driftCheckRef.current = context.currentTime;
      syncActive(next, context.currentTime, checkDrift);
      if (Math.abs(next - positionRef.current) >= 0.05 || next >= total) {
        positionRef.current = next;
        setPositionState(next);
      }
      if (next >= total) {
        setPlaying(false);
        for (const entry of mediaRef.current.values()) release(entry);
        mediaRef.current.clear();
        return;
      }
      frameRef.current = requestAnimationFrame(tick);
    };
    frameRef.current = requestAnimationFrame(tick);
    return () => {
      if (frameRef.current !== null) cancelAnimationFrame(frameRef.current);
      frameRef.current = null;
    };
  }, [playing, setPlaying, syncActive]);

  useEffect(
    () => () => {
      if (frameRef.current !== null) cancelAnimationFrame(frameRef.current);
      for (const entry of mediaRef.current.values()) release(entry);
      mediaRef.current.clear();
      if (contextRef.current) void contextRef.current.close();
      contextRef.current = null;
    },
    [],
  );

  return { playing, position, setPlaying, seek, stop };
}

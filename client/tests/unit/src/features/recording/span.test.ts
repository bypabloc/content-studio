import { describe, expect, it } from 'vitest';
import { MAX_SPAN, MIN_SPAN, clampSpan } from '@/features/recording/span';

describe('clampSpan (spec 010, D-4)', () => {
  it('exposes the limits of the span: 8 to 12 seconds', () => {
    expect([MIN_SPAN, MAX_SPAN]).toEqual([8, 12]);
  });

  it('keeps a span that already fits between 8 and 12 seconds', () => {
    expect(clampSpan(2, 12, 60)).toEqual({ start: 2, end: 12 });
  });

  it('grows a span shorter than 8 seconds from the same start', () => {
    expect(clampSpan(3, 5, 60)).toEqual({ start: 3, end: 11 });
  });

  it('shrinks a span longer than 12 seconds from the same start', () => {
    expect(clampSpan(1, 30, 60)).toEqual({ start: 1, end: 13 });
  });

  it('moves the span back so that it ends at the end of the file', () => {
    expect(clampSpan(18, 25, 20)).toEqual({ start: 12, end: 20 });
  });

  it('never asks for more seconds than the file has', () => {
    expect(clampSpan(0, 5, 6)).toEqual({ start: 0, end: 6 });
  });
});

import { describe, expect, it } from 'vitest';
import { FLOOR_DBFS, peakDbfs, rmsDbfs } from '@/features/recording/capture/levels';

describe('peakDbfs', () => {
  it('una muestra a fondo de escala es 0 dBFS', () => {
    expect(peakDbfs(Float32Array.from([0.1, -1, 0.5]))).toBeCloseTo(0, 6);
  });

  it('la mitad de la amplitud son unos -6 dBFS', () => {
    expect(peakDbfs(Float32Array.from([0.5, -0.25]))).toBeCloseTo(-6.02, 2);
  });

  it('el silencio no baja del suelo', () => {
    expect(peakDbfs(new Float32Array(480))).toBe(FLOOR_DBFS);
  });
});

describe('rmsDbfs', () => {
  it('una senoidal de amplitud 1 tiene 1/√2 de RMS: unos -3 dBFS', () => {
    const samples = Float32Array.from({ length: 48000 }, (_, i) => Math.sin((2 * Math.PI * 1000 * i) / 48000));

    expect(rmsDbfs(samples)).toBeCloseTo(-3.01, 1);
  });

  it('una señal constante de 0,5 da unos -6 dBFS', () => {
    expect(rmsDbfs(new Float32Array(100).fill(0.5))).toBeCloseTo(-6.02, 2);
  });

  it('el silencio no baja del suelo', () => {
    expect(rmsDbfs(new Float32Array(100))).toBe(FLOOR_DBFS);
  });
});

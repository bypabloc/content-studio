import { afterEach, describe, expect, it, vi } from 'vitest';
import { listMicrophones, microphoneOptions } from '@/features/recording/microphones';

function device(kind: MediaDeviceKind, deviceId: string, label: string): MediaDeviceInfo {
  return { kind, deviceId, label, groupId: 'grupo', toJSON: () => ({}) } as MediaDeviceInfo;
}

const unnamed = (n: number) => `Micrófono ${n}`;

afterEach(() => {
  vi.restoreAllMocks();
});

describe('microphoneOptions (spec 010, D-2)', () => {
  it('keeps only the audio inputs, in the order the system gives them', () => {
    const options = microphoneOptions(
      [device('audiooutput', 'salida-1', 'Altavoces'), device('audioinput', 'mic-1', 'HyperX'), device('audioinput', 'mic-2', 'Realtek')],
      unnamed,
    );

    expect(options).toEqual([
      { value: 'mic-1', label: 'HyperX' },
      { value: 'mic-2', label: 'Realtek' },
    ]);
  });

  it('names a microphone without label with the fallback, because the system hides the names until the permission', () => {
    expect(microphoneOptions([device('audioinput', 'mic-1', '')], unnamed)).toEqual([{ value: 'mic-1', label: 'Micrófono 1' }]);
  });
});

describe('listMicrophones (spec 010, D-2)', () => {
  it('asks for the microphone so the system gives the names, releases it, and lists the devices', async () => {
    const stop = vi.fn();
    const getUserMedia = vi.fn().mockResolvedValue({ getTracks: () => [{ stop }] });
    const enumerateDevices = vi.fn().mockResolvedValue([device('audioinput', 'mic-1', 'HyperX')]);
    Object.defineProperty(navigator, 'mediaDevices', { value: { getUserMedia, enumerateDevices }, configurable: true });

    const devices = await listMicrophones();

    expect(getUserMedia).toHaveBeenCalledWith({ audio: true });
    expect(stop).toHaveBeenCalledTimes(1);
    expect(devices.map((item) => item.label)).toEqual(['HyperX']);
  });
});

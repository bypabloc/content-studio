// Los micrófonos de entrada del sistema. Windows oculta sus nombres hasta que el micrófono se abre al menos una vez.

/** El micrófono elegido en Ajustes: vacío es el predeterminado de Windows. Va con `select.` para que «Restablecer» lo borre. */
export const MICROPHONE_SETTING = 'select.recording.microphone';

export type MicrophoneOption = { value: string; label: string };

/** Solo los micrófonos de entrada, con su nombre; si el sistema no da el nombre, «Micrófono N». */
export function microphoneOptions(devices: MediaDeviceInfo[], unnamed: (n: number) => string): MicrophoneOption[] {
  return devices
    .filter((device) => device.kind === 'audioinput')
    .map((device, index) => ({ value: device.deviceId, label: device.label || unnamed(index + 1) }));
}

/** Los dispositivos de audio del sistema. Abre el micrófono un instante para que Windows dé los nombres, y lo suelta. */
export async function listMicrophones(): Promise<MediaDeviceInfo[]> {
  const probe = await navigator.mediaDevices.getUserMedia({ audio: true });
  probe.getTracks().forEach((track) => track.stop());
  return navigator.mediaDevices.enumerateDevices();
}

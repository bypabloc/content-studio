import type { Job } from '@/shared/api/events';

/** Lo que pasa cuando un trabajo termina: el toast, la notificación de Windows y el sonido (AC-5). */
export interface Alerts {
  toast: (job: Job) => void;
  system: (job: Job) => void;
  ding: () => void;
}

export interface AlertOptions {
  /** La ventana tiene el foco: no hace falta avisar fuera de la app. */
  focused: boolean;
  /** Ajustes `notify.system` y `notify.sound`. */
  system: boolean;
  sound: boolean;
}

/** El toast sale siempre; la notificación de Windows y el sonido, solo sin foco y con su ajuste activo. */
export function announceFinished(job: Job, options: AlertOptions, alerts: Alerts): void {
  alerts.toast(job);
  if (options.focused) return;
  if (options.system) alerts.system(job);
  if (options.sound) alerts.ding();
}

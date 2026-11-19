import { isPermissionGranted, requestPermission, sendNotification } from '@tauri-apps/plugin-notification';
import { openPath } from '@tauri-apps/plugin-opener';
import { toast } from 'sonner';
import { t } from '@/shared/i18n/t';
import { ding } from './ding';
import type { Alerts } from './notify';

/** Los avisos de verdad: sonner para el toast (con «Abrir carpeta»), la notificación del sistema y el tono. */
export const tauriAlerts: Alerts = {
  toast: (job) => {
    const folder = job.output_dir;
    const action = folder ? { label: t('notify.open_folder'), onClick: () => void openPath(folder) } : undefined;
    if (job.status === 'done') toast.success(t('notify.done'), { action });
    else toast.error(t('notify.error'), { action });
  },
  system: (job) => {
    void (async () => {
      const allowed = (await isPermissionGranted()) || (await requestPermission()) === 'granted';
      if (allowed) sendNotification({ title: t('notify.system_title'), body: jobTitle(job) });
    })();
  },
  ding,
};

function jobTitle(job: { kind: string; id: number }): string {
  return job.kind === 'music' ? `${t('queue.kind.music')} #${job.id}` : `#${job.id}`;
}

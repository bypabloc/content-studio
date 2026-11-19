import { beforeEach, describe, expect, it, vi } from 'vitest';
import { isPermissionGranted, requestPermission, sendNotification } from '@tauri-apps/plugin-notification';
import { openPath } from '@tauri-apps/plugin-opener';
import { toast } from 'sonner';
import { tauriAlerts } from '@/shared/notify/alerts';
import type { Job } from '@/shared/api/events';
import { t } from '@/shared/i18n/t';

vi.mock('@tauri-apps/plugin-notification', () => ({
  isPermissionGranted: vi.fn(async () => true),
  requestPermission: vi.fn(async () => 'granted'),
  sendNotification: vi.fn(),
}));
vi.mock('@tauri-apps/plugin-opener', () => ({ openPath: vi.fn(async () => {}) }));
vi.mock('sonner', () => ({ toast: { success: vi.fn(), error: vi.fn() } }));

function job(status: 'done' | 'error', output_dir: string | null = null): Job {
  return {
    id: 9,
    kind: 'music',
    resource: 'gpu',
    status,
    position: 9,
    params: {},
    progress: 1,
    created_at: '2026-11-19T10:00:00Z',
    starred: false,
    output_dir,
  };
}

describe('tauriAlerts', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('un trabajo terminado muestra el toast de éxito con «Abrir carpeta»', () => {
    tauriAlerts.toast(job('done', 'out/music/x'));

    const [message, options] = vi.mocked(toast.success).mock.calls[0];
    const action = options?.action as { label: string; onClick: () => void };
    expect(message).toBe(t('notify.done'));
    expect(action.label).toBe(t('notify.open_folder'));
    action.onClick();
    expect(openPath).toHaveBeenCalledWith('out/music/x');
  });

  it('un trabajo con error muestra el toast de error, sin botón si no hay carpeta', () => {
    tauriAlerts.toast(job('error'));

    expect(toast.error).toHaveBeenCalledWith(t('notify.error'), { action: undefined });
  });

  it('la notificación del sistema pide permiso si hace falta y la envía con el nombre del trabajo', async () => {
    vi.mocked(isPermissionGranted).mockResolvedValueOnce(false);

    tauriAlerts.system(job('done'));

    await vi.waitFor(() => expect(sendNotification).toHaveBeenCalled());
    expect(requestPermission).toHaveBeenCalled();
    expect(sendNotification).toHaveBeenCalledWith({
      title: t('notify.system_title'),
      body: `${t('queue.kind.music')} #9`,
    });
  });
});

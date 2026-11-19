import { describe, expect, it, vi } from 'vitest';
import { announceFinished, type Alerts } from '@/shared/notify/notify';
import type { Job } from '@/shared/api/events';

const done: Job = {
  id: 7,
  kind: 'music',
  resource: 'gpu',
  status: 'done',
  position: 7,
  params: {},
  progress: 1,
  created_at: '2026-11-19T10:00:00Z',
  starred: false,
  output_dir: 'out/music/2026-11-19-7-lofi',
};

function alerts() {
  return { toast: vi.fn(), system: vi.fn(), ding: vi.fn() } satisfies Alerts;
}

describe('announceFinished', () => {
  it('siempre muestra el toast, aunque la ventana tenga el foco y los avisos estén apagados', () => {
    const avisos = alerts();

    announceFinished(done, { focused: true, system: false, sound: false }, avisos);

    expect(avisos.toast).toHaveBeenCalledWith(done);
    expect(avisos.system).not.toHaveBeenCalled();
    expect(avisos.ding).not.toHaveBeenCalled();
  });

  it('la notificación de Windows y el sonido salen solo sin foco y con el ajuste activo', () => {
    const avisos = alerts();

    announceFinished(done, { focused: false, system: true, sound: true }, avisos);

    expect(avisos.system).toHaveBeenCalledWith(done);
    expect(avisos.ding).toHaveBeenCalledOnce();
  });

  it('cada aviso se puede apagar por separado', () => {
    const avisos = alerts();

    announceFinished(done, { focused: false, system: false, sound: true }, avisos);

    expect(avisos.system).not.toHaveBeenCalled();
    expect(avisos.ding).toHaveBeenCalledOnce();
  });
});

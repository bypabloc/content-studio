import { useEffect } from 'react';
import { toast } from '@/shared/components/molecules/UIToast';
import { t } from '@/shared/i18n/t';
import { updateMessage, useUpdater, type UpdaterDeps } from './useUpdater';

/** Al abrir la app busca una versión nueva en segundo plano; si la hay, un aviso fijo ofrece actualizar (spec 022, D-6). */
export function useUpdateNotice(deps?: UpdaterDeps): void {
  const { state, running, check, install } = useUpdater(deps);

  useEffect(() => {
    void check();
  }, [check]);

  useEffect(() => {
    const message = updateMessage(state, running);
    if (state.kind === 'available' && message) {
      toast.info(message, { action: { label: t('update.install'), onClick: install }, persistent: true });
    } else if (state.kind === 'waiting' && message) {
      toast.info(message);
    }
    // Un aviso por cambio de estado: el número de trabajos solo cambia el texto de Ajustes > Acerca de.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [state.kind]);
}

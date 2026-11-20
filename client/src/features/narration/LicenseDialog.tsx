import { UIButton } from '@/shared/components/atoms/UIButton';
import { UIText } from '@/shared/components/atoms/UIText';
import { UIDialog } from '@/shared/components/organisms/UIDialog';
import { t } from '@/shared/i18n/t';

/**
 * El aviso de licencia antes de usar un motor con licencia no comercial (AC-7). Cancelar o Escape no cambia nada;
 * aceptar guarda la licencia. Vive en `features/narration` porque solo lo usa la narración.
 */
export function LicenseDialog({
  engine,
  license,
  commercial,
  onAccept,
  onCancel,
}: {
  engine: string;
  license: string;
  commercial: boolean;
  onAccept: () => void;
  onCancel: () => void;
}) {
  return (
    <UIDialog
      open
      onOpenChange={() => onCancel()}
      title={t('license.title', { engine })}
      closeLabel={t('ui.dialog.close')}
      footer={
        <>
          <UIButton variant="secondary" onClick={onCancel}>
            {t('license.cancel')}
          </UIButton>
          <UIButton onClick={onAccept}>{t('license.accept')}</UIButton>
        </>
      }
    >
      <UIText variant="body">
        {t('license.body', {
          license,
          usage: commercial ? t('license.usage.commercial') : t('license.usage.personal'),
        })}
      </UIText>
    </UIDialog>
  );
}

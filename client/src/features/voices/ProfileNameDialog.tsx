import { UIField } from '@/shared/components/molecules/UIField';
import { UIFormDialog } from '@/shared/components/organisms/UIFormDialog';
import { t } from '@/shared/i18n/t';

type Props = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  description: string;
  confirmLabel: string;
  value: string;
  onChange: (value: string) => void;
  pending: boolean;
  /** Mensaje de la API si el nombre no sirve (p. ej. un perfil que ya existe). */
  error?: string;
  onSubmit: () => void;
};

/**
 * Diálogo para crear o renombrar un perfil: un campo con el nombre visible. Confirmar no cierra el diálogo: lo cierra quien
 * lo abre cuando la API responde. El nombre vacío no se puede enviar (spec 010, D-6).
 */
export function ProfileNameDialog({ value, onChange, error, ...dialog }: Props) {
  return (
    <UIFormDialog {...dialog} cancelLabel={t('action.cancel')} confirmDisabled={value.trim() === ''}>
      <UIField
        label={t('voices.name')}
        value={value}
        maxLength={80}
        error={error}
        onChange={(event) => onChange(event.target.value)}
      />
    </UIFormDialog>
  );
}

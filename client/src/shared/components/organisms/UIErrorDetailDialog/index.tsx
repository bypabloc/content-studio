import { UIText } from '../../atoms/UIText';
import { UIDialog } from '../UIDialog';

type Props = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  /** Título del diálogo: es su nombre accesible. */
  title: string;
  /** El motivo en lenguaje llano (de su código). */
  message: string;
  /** El detalle técnico que dio el motor, para copiarlo a un reporte. */
  detail?: string | null;
  closeLabel: string;
};

/**
 * Un error de un trabajo: el motivo en lenguaje llano y, debajo, el detalle técnico (la salida del motor). El
 * detalle va como texto, no como HTML, así que un mensaje de ffmpeg no se interpreta.
 *
 * @author Pablo Contreras
 * @since 2026/11/22
 */
export function UIErrorDetailDialog({ open, onOpenChange, title, message, detail, closeLabel }: Props): React.JSX.Element {
  return (
    <UIDialog open={open} onOpenChange={onOpenChange} title={title} closeLabel={closeLabel}>
      <UIText variant="body">{message}</UIText>
      {detail ? <UIText variant="caption">{detail}</UIText> : null}
    </UIDialog>
  );
}

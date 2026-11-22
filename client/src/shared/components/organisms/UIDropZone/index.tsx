import { cn } from 'cn';

import { UIBox } from '../../atoms/UIBox';
import { UIButton } from '../../atoms/UIButton';
import { UIText } from '../../atoms/UIText';

type Props = {
  /** Mientras hay archivos sobre la ventana, la zona se resalta. */
  dragging: boolean;
  title: string;
  hint: string;
  actionLabel: string;
  onPick: () => void;
};

/**
 * La zona grande de «soltar archivos aquí»: el borde se marca mientras algo está sobre la ventana y su botón abre el
 * diálogo del sistema. Las rutas llegan por el arrastre de Tauri (`useFilePaths`), no por esta zona.
 *
 * @author Pablo Contreras
 * @since 2026/11/22
 */
export function UIDropZone({ dragging, title, hint, actionLabel, onPick }: Props): React.JSX.Element {
  return (
    <UIBox
      data-dragging={dragging ? 'true' : undefined}
      className={cn(
        'flex min-h-32 flex-col items-center justify-center gap-2 rounded-xl border-2 border-dashed px-4 py-6 text-center',
        'transition-colors duration-200 motion-reduce:transition-none',
        dragging ? 'border-primary bg-primary/5' : 'border-input bg-card',
      )}
    >
      <UIText variant="body">{title}</UIText>
      <UIText variant="caption">{hint}</UIText>
      <UIButton variant="secondary" onClick={onPick}>
        {actionLabel}
      </UIButton>
    </UIBox>
  );
}

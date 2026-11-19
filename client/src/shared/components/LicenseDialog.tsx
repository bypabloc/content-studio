import { useEffect, useId, useRef } from 'react';
import { t } from '@/shared/i18n/t';

/**
 * El aviso de licencia antes de usar un motor con licencia no comercial (AC-7). Cancelar o Escape no cambia nada;
 * aceptar guarda la licencia. Es un diálogo propio: los controles de shadcn aún no se copian (`ui-components.md`).
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
  const titleId = useId();
  const acceptButton = useRef<HTMLButtonElement>(null);
  useEffect(() => acceptButton.current?.focus(), []);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-background/70"
      onKeyDown={(event) => {
        if (event.key === 'Escape') onCancel();
      }}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        className="w-full max-w-md rounded-lg border border-border bg-card p-5 text-card-foreground shadow-lg"
      >
        <h3 id={titleId} className="text-base font-semibold">
          {t('license.title', { engine })}
        </h3>
        <p className="mt-2 text-sm">
          {t('license.body', {
            license,
            usage: commercial ? t('license.usage.commercial') : t('license.usage.personal'),
          })}
        </p>
        <div className="mt-4 flex justify-end gap-2">
          <button
            type="button"
            onClick={onCancel}
            className="rounded-md border border-border px-3 py-1.5 text-sm hover:bg-accent"
          >
            {t('license.cancel')}
          </button>
          <button
            ref={acceptButton}
            type="button"
            onClick={onAccept}
            className="rounded-md bg-primary px-3 py-1.5 text-sm text-primary-foreground"
          >
            {t('license.accept')}
          </button>
        </div>
      </div>
    </div>
  );
}

import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { LicenseDialog } from '@/shared/components/LicenseDialog';
import { t } from '@/shared/i18n/t';

afterEach(cleanup);

describe('LicenseDialog', () => {
  it('nombra el motor, explica su licencia y deja aceptarla o cancelarla', () => {
    const onAccept = vi.fn();
    const onCancel = vi.fn();
    render(
      <LicenseDialog engine="omnivoice" license="CC-BY-NC-4.0" commercial={false} onAccept={onAccept} onCancel={onCancel} />,
    );

    const dialog = screen.getByRole('dialog', { name: t('license.title', { engine: 'omnivoice' }) });
    expect(dialog.textContent).toContain('CC-BY-NC-4.0');
    expect(dialog.textContent).toContain(t('license.usage.personal'));
    fireEvent.click(screen.getByRole('button', { name: t('license.accept') }));
    expect(onAccept).toHaveBeenCalledTimes(1);
    fireEvent.click(screen.getByRole('button', { name: t('license.cancel') }));
    expect(onCancel).toHaveBeenCalledTimes(1);
  });

  it('una licencia comercial dice que se puede usar en proyectos comerciales', () => {
    render(
      <LicenseDialog engine="voxcpm2" license="Apache-2.0" commercial onAccept={() => {}} onCancel={() => {}} />,
    );

    expect(screen.getByRole('dialog').textContent).toContain(t('license.usage.commercial'));
  });

  it('Escape cancela', () => {
    const onCancel = vi.fn();
    render(
      <LicenseDialog engine="omnivoice" license="CC-BY-NC-4.0" commercial={false} onAccept={() => {}} onCancel={onCancel} />,
    );

    fireEvent.keyDown(screen.getByRole('dialog'), { key: 'Escape' });

    expect(onCancel).toHaveBeenCalledTimes(1);
  });

  it('otras teclas no cancelan el aviso', () => {
    const onCancel = vi.fn();
    render(
      <LicenseDialog engine="omnivoice" license="CC-BY-NC-4.0" commercial={false} onAccept={() => {}} onCancel={onCancel} />,
    );

    fireEvent.keyDown(screen.getByRole('dialog'), { key: 'Enter' });

    expect(onCancel).not.toHaveBeenCalled();
  });
});

import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { Ruler } from '@/features/editor/Ruler';
import { t } from '@/shared/i18n/t';

afterEach(cleanup);

describe('Ruler', () => {
  it('muestra la regla accesible, los marcadores y el cabezal', () => {
    render(
      <Ruler
        duration={12}
        zoom={80}
        playhead={2}
        markers={[{ id: 'marker-1', t: 10, label: 'corte', color: '#f00' }]}
      />,
    );
    expect(screen.getByRole('group', { name: t('editor.timeline.ruler') })).toBeTruthy();
    expect(screen.getByText('corte')).toBeTruthy();
    expect(screen.getByRole('img', { name: t('editor.timeline.position') })).toBeTruthy();
  });

  it('selecciona un marcador y permite renombrarlo con doble clic', () => {
    const onMarkerSelect = vi.fn();
    const onMarkerRename = vi.fn();
    render(
      <Ruler
        duration={12}
        zoom={80}
        playhead={2}
        markers={[{ id: 'marker-1', t: 10, label: 'corte', color: '#f00' }]}
        onMarkerSelect={onMarkerSelect}
        onMarkerRename={onMarkerRename}
      />,
    );
    const marker = screen.getByRole('button', { name: 'corte' });
    fireEvent.click(marker);
    expect(onMarkerSelect).toHaveBeenCalledWith('marker-1');
    fireEvent.doubleClick(marker);
    const label = screen.getByRole('textbox', { name: t('editor.marker.rename') });
    fireEvent.change(label, { target: { value: 'fin' } });
    fireEvent.keyDown(label, { key: 'Enter' });
    expect(onMarkerRename).toHaveBeenCalledWith('marker-1', 'fin');
  });

  it('activa el marcador con teclado y descarta nombres vacíos o cancelados', () => {
    const onMarkerSelect = vi.fn();
    const onMarkerRename = vi.fn();
    render(
      <Ruler
        duration={12}
        zoom={80}
        playhead={2}
        markers={[{ id: 'marker-1', t: 10, label: 'corte', color: '#f00' }]}
        selectedMarker="marker-1"
        onMarkerSelect={onMarkerSelect}
        onMarkerRename={onMarkerRename}
      />,
    );
    const marker = screen.getByRole('button', { name: 'corte' });
    expect(marker.getAttribute('aria-pressed')).toBe('true');
    fireEvent.keyDown(marker, { key: 'Enter' });
    fireEvent.keyDown(marker, { key: ' ' });
    expect(onMarkerSelect).toHaveBeenCalledTimes(2);

    fireEvent.doubleClick(marker);
    const label = screen.getByRole('textbox', { name: t('editor.marker.rename') });
    fireEvent.change(label, { target: { value: '   ' } });
    fireEvent.keyDown(label, { key: 'Enter' });
    expect(onMarkerRename).not.toHaveBeenCalled();

    fireEvent.doubleClick(screen.getByRole('button', { name: 'corte' }));
    const secondLabel = screen.getByRole('textbox', { name: t('editor.marker.rename') });
    fireEvent.change(secondLabel, { target: { value: ' Fin ' } });
    fireEvent.keyDown(secondLabel, { key: 'Escape' });
    expect(onMarkerRename).not.toHaveBeenCalled();
  });
});

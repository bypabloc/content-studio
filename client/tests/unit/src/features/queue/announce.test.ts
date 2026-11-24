import { describe, expect, it } from 'vitest';
import { reorderAccessibility } from '@/features/queue/announce';

// Lo que el lector de pantalla oye al reordenar la cola con el teclado: los textos salen de es.json.
describe('reorderAccessibility', () => {
  const accessibility = reorderAccessibility([2, 3]);

  it('las instrucciones dicen cómo reordenar con el teclado', () => {
    expect(accessibility.screenReaderInstructions.draggable).toContain('Espacio');
    expect(accessibility.screenReaderInstructions.draggable).toContain('Escape');
  });

  it('anuncia tomar, mover, soltar y cancelar, con el lugar del trabajo en la cola', () => {
    const { announcements } = accessibility;
    expect(announcements.onDragStart()).toBe('Trabajo tomado. Usa las flechas para moverlo.');
    expect(announcements.onDragOver({ over: { id: 2 } })).toBe('Trabajo sobre la posición 1 de 2.');
    expect(announcements.onDragEnd({ over: { id: 3 } })).toBe('Trabajo soltado en la posición 2 de 2.');
    expect(announcements.onDragCancel()).toBe('Reordenar cancelado.');
  });

  it('sin un destino no anuncia ningún lugar', () => {
    expect(accessibility.announcements.onDragOver({ over: null })).toBeUndefined();
    expect(accessibility.announcements.onDragEnd({ over: null })).toBeUndefined();
  });
});

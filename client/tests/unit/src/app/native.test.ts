import { describe, expect, it } from 'vitest';
import { blockContextMenu } from '@/app/native';

// D-8: el menú contextual solo sale donde la pantalla lo marca con data-allow-context.
function rightClick(target: HTMLElement): boolean {
  const listener = (event: MouseEvent) => blockContextMenu(event);
  document.addEventListener('contextmenu', listener);
  const event = new MouseEvent('contextmenu', { bubbles: true, cancelable: true });
  target.dispatchEvent(event);
  document.removeEventListener('contextmenu', listener);
  return event.defaultPrevented;
}

describe('blockContextMenu', () => {
  it('bloquea el menú contextual en la app', () => {
    const plain = document.createElement('div');
    document.body.append(plain);
    expect(rightClick(plain)).toBe(true);
    plain.remove();
  });

  it('lo deja salir dentro de un elemento marcado con data-allow-context', () => {
    const area = document.createElement('div');
    area.setAttribute('data-allow-context', '');
    const child = document.createElement('span');
    area.append(child);
    document.body.append(area);
    expect(rightClick(child)).toBe(false);
    area.remove();
  });
});

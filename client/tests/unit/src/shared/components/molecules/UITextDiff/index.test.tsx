import { cleanup, render } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';

import { UITextDiff, wordDiff } from '@/shared/components/molecules/UITextDiff';

afterEach(cleanup);

describe('UITextDiff (spec 021, D-5)', () => {
  it('wordDiff deja las palabras iguales y agrupa cada tramo distinto', () => {
    expect(wordDiff('Tienes 24 horas; es DEMO.', 'Tienes veinticuatro horas; es demo.')).toEqual([
      { same: 'Tienes' },
      { removed: '24', added: 'veinticuatro' },
      { same: 'horas;' },
      { same: 'es' },
      { removed: 'DEMO.', added: 'demo.' },
    ]);
    expect(wordDiff('a b c', 'a b c')).toEqual([{ same: 'a' }, { same: 'b' }, { same: 'c' }]);
    expect(wordDiff('a', '')).toEqual([{ removed: 'a', added: '' }]);
    expect(wordDiff('', 'b')).toEqual([{ removed: '', added: 'b' }]);
  });

  it('muestra lo quitado tachado y lo nuevo agregado', () => {
    const { container } = render(<UITextDiff before="Tienes 24 horas." after="Tienes veinticuatro horas." />);
    expect(container.querySelector('del')?.textContent).toBe('24');
    expect(container.querySelector('ins')?.textContent).toBe('veinticuatro');
    expect(container.textContent).toContain('Tienes');
  });

  it('deja un espacio después de un tramo cambiado, sin pegarlo a la palabra siguiente', () => {
    const { container } = render(<UITextDiff before="Son 3 pasos; nada más." after="Son 3 pasos. Nada más." />);
    expect(container.textContent).toContain('Nada más.');
  });
});

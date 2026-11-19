import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { App, APP_VERSION } from '@/app/App';

describe('App', () => {
  it('muestra el nombre y la versión del catálogo', () => {
    render(<App />);

    expect(screen.getByRole('heading').textContent).toBe('Content Studio');
    expect(screen.getByText(`Versión ${APP_VERSION}`)).toBeTruthy();
  });
});

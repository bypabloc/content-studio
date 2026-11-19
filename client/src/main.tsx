import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { App } from '@/app/App';
import { Providers } from '@/app/Providers';
import './index.css';

// Sensación de app nativa (D-8): sin menú contextual salvo donde se marque data-allow-context.
document.addEventListener('contextmenu', (event) => {
  if (!(event.target instanceof Element && event.target.closest('[data-allow-context]'))) event.preventDefault();
});

createRoot(document.getElementById('root') as HTMLElement).render(
  <StrictMode>
    <Providers>
      <App />
    </Providers>
  </StrictMode>,
);

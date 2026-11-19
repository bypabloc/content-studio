import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { App } from '@/app/App';
import { blockContextMenu } from '@/app/native';
import './index.css';

// Sensación de app nativa (D-8): sin menú contextual salvo donde se marque data-allow-context. Va una sola vez, aquí.
document.addEventListener('contextmenu', blockContextMenu);

createRoot(document.getElementById('root') as HTMLElement).render(
  <StrictMode>
    <App />
  </StrictMode>,
);

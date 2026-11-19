# 005: @dnd-kit para reordenar la cola (dependencia nueva)

- **Contexto**: los trabajos en espera se reordenan arrastrando (AC-6). El arrastre nativo de HTML5 no tiene accesibilidad de teclado, y la cola tiene que poder reordenarse sin ratón.
- **Elegida**: `@dnd-kit/core` 6.3.1 y `@dnd-kit/sortable` 10.0.0 (exactas), con `@dnd-kit/utilities` 3.2.2 para el `transform`. El orden se calcula con `moveQueued` y `dropOrder` (`client/src/features/queue/order.ts`), que son funciones puras.
- **Descartadas**: el arrastre nativo de HTML5 (sin teclado); escribir el arrastre a mano con pointer events (más código y más casos que probar).
- **Cómo revertir**: reemplazar `QueuePanel` por botones de subir y bajar que llamen a `queue.reorder` con el mismo orden.
- **Cómo comprobarla**: `cd client && bun run test` (`QueuePanel.test.tsx` dispara el fin del arrastre; `order.test.ts` prueba el orden).
- **Antes de**: el merge a `dev`. El arrastre con el ratón no lo prueba ningún test (el e2e cubre el teclado); queda en `PENDING/005-arrastre-raton`.

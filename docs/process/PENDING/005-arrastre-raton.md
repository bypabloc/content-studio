# 005: el arrastre con el ratón de la cola no tiene prueba automática

- **Qué**: el reordenado con el ratón (dnd-kit con `PointerSensor`) no lo prueba ningún test. `QueuePanel.test.tsx` dispara el fin del arrastre a mano, y el e2e `queue/happy-reorder-pause-cancel-retry` cubre el teclado.
- **Por qué no se hizo**: un arrastre real con Playwright sobre dnd-kit es frágil sin esperas fijas, y el teclado ya cubre el AC-6 de accesibilidad.
- **Cuándo**: después del merge a `dev`, junto con la revisión visual de la cola.
- **Quién**: agente.
- **Qué la cierra**: un e2e `queue/happy-reorder-mouse` que arrastre una fila en espera sobre otra y compruebe el `PUT /queue/order`.

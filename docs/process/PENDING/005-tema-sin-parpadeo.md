# 005: AC-2, «al reabrir la app no hay parpadeo», sin prueba automática

- **Qué**: `client/public/theme-init.js` pinta el tema antes de que cargue React, para que no haya parpadeo. Ningún test lo comprueba: jsdom no pinta, y el e2e corre sobre `vite preview` sin reabrir la ventana.
- **Por qué no se hizo**: el parpadeo solo se ve en la ventana real de Tauri, al arrancar.
- **Cuándo**: en la verificación real de la app (T9) y antes del merge a `main`.
- **Quién**: usuario, mirando la ventana al reabrirla con el tema oscuro fijo.
- **Qué la cierra**: confirmar que la app abre directamente en el tema guardado, sin el flash del contrario.

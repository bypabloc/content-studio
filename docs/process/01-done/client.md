---
modulo: cliente
actualizada: 2026-11-19
---

# Cliente de escritorio (Tauri)

## Qué resuelve

La ventana de escritorio Content Studio: levanta el server, muestra la barra lateral con las secciones, la cola de trabajos con su progreso en vivo y los ajustes. Es la base donde cada spec agrega su sección.

## Qué hace hoy

- Tauri 2 arranca `studio serve` con un token por sesión, lee su línea `ready` y lo cierra con la ventana. En Windows, un Job Object lo mata aunque la app se cierre mal.
- La API se pide con un cliente tipado desde OpenAPI (`shared/api/schema.d.ts`) y TanStack Query. Los eventos SSE actualizan la caché sin volver a pedir datos.
- Cola: ver, reordenar con el ratón o el teclado (anuncios en español), pausar, cancelar y reintentar. Al terminar un trabajo avisa con un toast, y sin foco también con notificación y sonido (desactivables).
- Selectores con ★ en la opción recomendada que recuerdan la última elección (tabla `settings`).
- Ajustes: tema claro, oscuro o del sistema; avisos; restablecer elecciones y atajos (Ctrl+K, Ctrl+Enter, Espacio).
- Los textos visibles salen de `client/messages/es.json` con `t()`. El lint no deja literales en JSX.

## Dónde vive

- Código: `client/src/{app,features,shared}` y el Rust en `client/src-tauri/src/` (`server.rs`, `lib.rs`).
- Gates: `client-lint`, `client-typecheck`, `client-unit` (con la auditoría del espejo y la cobertura), `budget` (`client/budget.json`), `e2e` (`tests/e2e/`) y `tauri-check` (`cargo check`).

## Historial

- 2026-11-19: ficha inicial con la spec 005 (client Tauri base: shell, tema, cola, selector y ajustes).

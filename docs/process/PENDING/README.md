# Revisiones pendientes que no bloquean

Lo que se revisa **después** y no impide pasar a `main`: una observación de la verificación, una mejora que quedó fuera de alcance, una escucha comparada que el usuario hará con calma. Cada ficha dice cuándo toca, quién la hace y qué la cierra, y se borra al cerrarla, con su fila. Lo que sí bloquea va en [`../WARNING/`](../WARNING/README.md).

Nombre: `<spec>-<tema>.md`. Formato:

```markdown
# <spec>: <qué revisar en una línea>

- **Qué**: la observación o el pendiente.
- **Por qué no se hizo**: fuera de alcance, falta un dato, decisión del usuario.
- **Cuándo**: antes o después de publicar; con qué spec o evento.
- **Quién**: agente o usuario.
- **Qué la cierra**: comando, prueba o decisión.
```

| Ficha | Qué | Cuándo | Quién |
| :--- | :--- | :--- | :--- |
| [001-duracion-de-audio](001-duracion-de-audio.md) | La duración de música y narración no coincide con la pedida (igual en `dev`) | Antes de publicar el lote | Usuario y agente |
| [002-cspell-excepciones-temporales](002-cspell-excepciones-temporales.md) | Exclusiones de cspell que quedan a propósito: `grabar/` (010) y textos en español de D-1 | La 010 | Agente |
| [002-nombres-en-disco](002-nombres-en-disco.md) | `aprobacion.json` de las voces construidas sigue en español | Antes de publicar, o en la 004 | Usuario y agente |
| [003-bajar-baselines](003-bajar-baselines.md) | Vaciar los baselines de tamaño, espejo y cobertura, y los overrides de mypy, a medida que se tocan los archivos | En cada spec que toque un módulo de la lista; `grabar/` (010) | Agente |
| [004-db-antes-del-subcomando](004-db-antes-del-subcomando.md) | `studio --db` solo se acepta antes del subcomando | La 010 o la 011 | Agente |
| [004-eventos-cli-sin-sse](004-eventos-cli-sin-sse.md) | Los cambios de la CLI sobre trabajos que el server no corre no salen por SSE | Antes de la 005 | Agente |
| [004-httpx-deprecado](004-httpx-deprecado.md) | `starlette.testclient` avisa que httpx 0.28 está deprecado | Cuando starlette soporte httpx nuevo | Agente |
| [005-node-modules-del-principal](005-node-modules-del-principal.md) | El node_modules del principal recibió dependencias del worktree 005 (regenerable) | Después del lote | Usuario |
| [005-grafo-client](005-grafo-client.md) | graphify no indexa client/src (D-10 lo pedía) | Después de la 005 | Agente |
| [005-arrastre-raton](005-arrastre-raton.md) | El arrastre con el ratón de la cola no tiene prueba automática | Después del merge a dev | Agente |
| [005-avisos-sonner-ingles](005-avisos-sonner-ingles.md) | Sonner pone en inglés su región de avisos, y el anuncio de reordenar sin destino no borra el anterior | Después de la 005 | Agente |
| [005-tema-sin-parpadeo](005-tema-sin-parpadeo.md) | AC-2 (sin parpadeo al reabrir) no tiene prueba automática: se mira en la app | T9 y antes de main | Usuario |
| [005-avisos-foco](005-avisos-foco.md) | El cableado de los avisos (sin foco y con ajuste) no tiene prueba | Después de la 005 | Agente |
| [005-worktree-enlaces-rotos](005-worktree-enlaces-rotos.md) | `worktree` no limpia enlaces rotos y `close` falla si la carpeta se borró a mano | Después de la 005 | Agente |
| [005-stop-durante-arranque](005-stop-durante-arranque.md) | Cerrar la ventana mientras el server arranca puede esperar hasta 30 s | Después de la 005 | Agente |
| [005-desvios-d1-d8](005-desvios-d1-d8.md) | Desvíos de shadcn, plugin-dialog, CSP, Geist y theme-init frente a D-1, D-2, D-4 y D-8 | Antes de la 022 y según cada sección | Agente |
| [005-aviso-windows-y-sonido](005-aviso-windows-y-sonido.md) | AC-5: la notificación de Windows y el sonido con la ventana minimizada no se comprobaron en la app real | Al primer uso real o antes de la 022 | Usuario |
| [shell-guard-codex-antigravity](shell-guard-codex-antigravity.md) | El bloqueo de `sleep` y `wsl` no se probó en Codex ni en Antigravity | Al usar esas herramientas | Usuario |

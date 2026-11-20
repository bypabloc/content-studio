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
| [002-nombres-en-disco](002-nombres-en-disco.md) | `aprobacion.json` de las voces construidas sigue en español | Antes de publicar, o en la 004 | Usuario y agente |
| [003-bajar-baselines](003-bajar-baselines.md) | Vaciar los baselines de tamaño, espejo y cobertura, y los overrides de mypy, a medida que se tocan los archivos | En cada spec que toque un módulo de la lista | Agente |
| [004-db-antes-del-subcomando](004-db-antes-del-subcomando.md) | `studio --db` solo se acepta antes del subcomando | La 010 o la 011 | Agente |
| [004-eventos-cli-sin-sse](004-eventos-cli-sin-sse.md) | Los cambios de la CLI sobre trabajos que el server no corre no salen por SSE | Antes de la 005 | Agente |
| [004-httpx-deprecado](004-httpx-deprecado.md) | `starlette.testclient` avisa que httpx 0.28 está deprecado | Cuando starlette soporte httpx nuevo | Agente |
| [005-node-modules-del-principal](005-node-modules-del-principal.md) | El node_modules del principal recibió dependencias del worktree 005 (regenerable) | Después del lote | Usuario |
| [005-grafo-client](005-grafo-client.md) | graphify no indexa client/src (D-10 lo pedía) | Después de la 005 | Agente |
| [005-arrastre-raton](005-arrastre-raton.md) | El arrastre con el ratón de la cola no tiene prueba automática | Después del merge a dev | Agente |
| [005-avisos-sonner-ingles](005-avisos-sonner-ingles.md) | El anuncio de reordenar sin destino no borra el anterior (la región de sonner la cerró la 007) | Después de la 005 | Agente |
| [005-tema-sin-parpadeo](005-tema-sin-parpadeo.md) | AC-2 (sin parpadeo al reabrir) no tiene prueba automática: se mira en la app | T9 y antes de main | Usuario |
| [005-avisos-foco](005-avisos-foco.md) | El cableado de los avisos (sin foco y con ajuste) no tiene prueba | Después de la 005 | Agente |
| [005-worktree-enlaces-rotos](005-worktree-enlaces-rotos.md) | `worktree` no limpia enlaces rotos y `close` falla si la carpeta se borró a mano | Después de la 005 | Agente |
| [005-stop-durante-arranque](005-stop-durante-arranque.md) | Cerrar la ventana mientras el server arranca puede esperar hasta 30 s | Después de la 005 | Agente |
| [005-desvios-d1-d8](005-desvios-d1-d8.md) | Desvíos de shadcn, plugin-dialog, CSP, Geist y theme-init frente a D-1, D-2, D-4 y D-8 | Antes de la 022 y según cada sección | Agente |
| [005-aviso-windows-y-sonido](005-aviso-windows-y-sonido.md) | AC-5: la notificación de Windows y el sonido con la ventana minimizada no se comprobaron en la app real | Al primer uso real o antes de la 022 | Usuario |
| [006-cli-carpeta-compartida](006-cli-carpeta-compartida.md) | Con `--output archivo.wav`, dos tomas en una misma carpeta comparten `blocks/` y `script.json` | Después de publicar, o antes si la 010 o la 011 usan la CLI en lote | Agente |
| [006-evaluar-toma-regenerada](006-evaluar-toma-regenerada.md) | Evaluar con whisper solo el párrafo regenerado, sin reintentar los bloques ajenos | Antes de elegir una toma por su evaluación | Agente |
| [006-referencia-en-disco](006-referencia-en-disco.md) | Regenerar relee el audio de referencia del disco en cada petición (sin caché) | Después de cerrar la 006 | Agente |
| [007-errores-validacion](007-errores-validacion.md) | Los 422 de validación de FastAPI salen en inglés y fuera del catálogo | Después de la 007, con la primera pantalla que los muestre | Agente |
| [007-revision-humana-en-pt](007-revision-humana-en-pt.md) | Una persona revisa `en.json` y `pt.json`, que los tradujo el agente | Después de la 007, antes de la primera versión en `main` | Usuario |
| [007-plurales](007-plurales.md) | Los textos que dependen de un número no tienen formas de plural (`_one`, `_other`) | En la primera spec con un texto de número | Agente |
| [007-contraste-oscuro](007-contraste-oscuro.md) | El texto del botón primario en tema oscuro tiene poco contraste en la revisión visual | Después de la 007 | Agente |
| [007-soltar-antes-del-catalogo](007-soltar-antes-del-catalogo.md) | Soltar guiones antes de que cargue el catálogo de motores los descarta sin aviso | En la spec de importación de guiones | Agente |
| [shell-guard-codex-antigravity](shell-guard-codex-antigravity.md) | El bloqueo de `sleep` y `wsl` no se probó en Codex ni en Antigravity | Al usar esas herramientas | Usuario |
| [008-revision-visual-organismos](008-revision-visual-organismos.md) | Las celdas, el asa y el título de los organismos adaptados, el reproductor (44 px) y el aviso de licencia no se miraron en la app | La T5 y la T6 | Agente y usuario |
| [008-sincronizar-con-klinikae](008-sincronizar-con-klinikae.md) | Cómo traer las mejoras de klinikae: copiar a mano, un script de diff o un paquete compartido | Cuando haya que traer un cambio | Usuario |
| [008-uitext-className](008-uitext-className.md) | `UIText` acepta `className` y 15 usos de features/app ajustan peso y tamaño: decidir si lo conserva | Después de la 009 | Agente |
| [008-underscore-row](008-underscore-row.md) | `_row` en UIRowTable y UIRepeatGroup da avisos de no-underscore-dangle (no bloquean) | Al tocar esos organismos o antes de la 022 | Agente |
| [009-abrir-carpeta](009-abrir-carpeta.md) | «Abrir carpeta» (solo ícono, D-5) no tiene botón hoy en Narración ni en la cola: no hay carpeta que mostrar | Cuando una pantalla muestre la carpeta de salida | Agente |
| [010-grabar-con-microfono-real](010-grabar-con-microfono-real.md) | La grabación con un micrófono real (permiso, medidor, prueba de sala, 48 kHz) no se ha probado en la app | Antes de publicar la 010 (T9) | Usuario |
| [010-contraste-tema-oscuro](010-contraste-tema-oscuro.md) | Contraste del tema oscuro en Mis voces y el catálogo: medir y decidir (tokens del design system) | Después de publicar la 010 | Agente |
| [010-whisper-a-faster-whisper](010-whisper-a-faster-whisper.md) | El chequeo y la evaluación de tomas usan openai-whisper; la 013 pasa a faster-whisper | En la 013 | Agente |
| [010-construir-voces-reales](010-construir-voces-reales.md) | El build real del catálogo sobre las voces del usuario (AC-7): decidir voces y ejecutar | Cuando el usuario lo pida; no bloquea el merge | Usuario |

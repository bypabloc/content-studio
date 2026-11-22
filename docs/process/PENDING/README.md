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
| [010-contraste-tema-oscuro](010-contraste-tema-oscuro.md) | Contraste del tema oscuro en Mis voces y el catálogo: medir y decidir (tokens del design system) | Después de publicar la 010 | Agente |
| [013-receta-cosyvoice](013-receta-cosyvoice.md) | La receta de CosyVoice sigue instalando openai-whisper sin comprobar si lo usa | Antes de la próxima instalación de CosyVoice | Agente |
| [013-escucha-y-revision-manual](013-escucha-y-revision-manual.md) | Escuchar el limpio y los subtítulos, revisar la UI real y probar EDL y XML en un editor | Después del merge a dev; no bloquea | Usuario |
| [010-construir-voces-reales](010-construir-voces-reales.md) | El build real del catálogo sobre las voces del usuario (AC-7): decidir voces y ejecutar | Cuando el usuario lo pida; no bloquea el merge | Usuario |
| [011-generar-muestras](011-generar-muestras.md) | Generar las 126 muestras de 10 s del buscador (corrida larga en GPU) | Después del merge a dev | Agente o usuario |
| [011-escucha-muestras](011-escucha-muestras.md) | Escuchar `lofi-chill`: el espectrograma muestra transitorios; el gusto lo decide el usuario | Antes de generar las 126 | Usuario |
| [011-caida-agudos-corporate](011-caida-agudos-corporate.md) | La pista corporate-minimal v2 pierde los agudos desde ~19.5 s (escucha del usuario) | Antes de usarla en un video | Usuario |
| [012-instalar-motor-real](012-instalar-motor-real.md) | Revisión visual de la UI con datos temporales (bienvenida, winget, traslado) y capturas; la e2e y el CLI ya pasan | Después del merge a dev; no bloquea | Usuario |
| [012-grafo-server](012-grafo-server.md) | Reconstruir el índice de graphify cuando se pueda leer la exclusión global de Git | Antes de una búsqueda nueva del server | Agente |
| [lote-huerfanas-bloqueadas](lote-huerfanos-bloqueadas.md) | 8 carpetas huérfanas de `content-studio-worktrees/` con ACL de administrador; las borra el usuario con terminal elevada | Cuando el usuario lo pida; no bloquea | Usuario |
| [014-escucha-y-revision](014-escucha-y-revision.md) | Escuchar la narración alineada, revisar la sincronía, la UI real y los presets incluidos (gusto) | Después del merge a dev; no bloquea | Usuario |
| [014-audio-quemar-copia](014-audio-quemar-copia.md) | Al quemar, el audio PCM de un MOV no se ha probado: la copia del audio puede fallar en MP4 | En la verificación final (T9) | Agente |
| [014-traduccion-real](014-traduccion-real.md) | Falta la prueba `-m local` automatizada de la traducción con `small`; la corrida real y el cierre ya están verificados a mano | Después del merge a dev; no bloquea | Agente |
| [014-capturas-editor](014-capturas-editor.md) | Capturas del editor (claro y oscuro) y cuadros de la quema, comparados con `image-reader` (batería 03, puntos 3 y 9) | Después del merge a dev; no bloquea | Agente |
| [015-bitrates-presets](015-bitrates-presets.md) | Los bitrates máximos por plataforma de los presets de redes (D-2) faltan, con sus fuentes | Antes de la verificación final de 015 (T9) | Agente |
| [015-foto-de-prueba](015-foto-de-prueba.md) | La prueba `-m local` de cara real se salta: falta una foto con licencia clara en `server/tests/fixtures/vision/` | Antes de la verificación final de 015 (T9) | Usuario |
| [015-refactor-masterizacion-narracion](015-refactor-masterizacion-narracion.md) | La masterización de la narración repite las dos pasadas de `normalize.py`; migrarla cambia su salida (commit aparte) | Después del merge de 015; no bloquea | Agente |
| [015-repair-primera-instalacion](015-repair-primera-instalacion.md) | `repair` rechaza un motor cuya primera instalación no terminó (`engine_external`); de la spec 009 | Después del merge de 015; no bloquea | Agente |

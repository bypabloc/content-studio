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
| [026-reintentar-cosyvoice3](026-reintentar-cosyvoice3.md) | cosyvoice3 en 3.12 o más, y escucha de onnxruntime 1.23.2 | después de publicar | agente y usuario |
| [026-reintentar-indextts](026-reintentar-indextts.md) | indextts: aceptar la licencia y verificar 3.11 | antes de publicar | usuario y agente |
| [026-chatterbox-volumen-y-cangjie](026-chatterbox-volumen-y-cangjie.md) | chatterbox: aviso de LUFS del mastering y mapa Cangjie | antes de publicar | usuario y agente |
| [026-reintentar-voxcpm2](026-reintentar-voxcpm2.md) | voxcpm2 en 3.15 con rueda cp315 de pyahocorasick | después de publicar | agente |
| [026-reintentar-qwen-0.6b](026-reintentar-qwen-0.6b.md) | qwen-0.6b en 3.15 con onnxruntime cp315 | después de publicar | agente |
| [026-reintentar-qwen-1.7b](026-reintentar-qwen-1.7b.md) | qwen-1.7b en 3.15 con onnxruntime cp315 | después de publicar | agente |
| [026-reintentar-omnivoice](026-reintentar-omnivoice.md) | omnivoice: aceptar licencia, probar 3.15 y la revisión nueva | antes de publicar | usuario y agente |
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
| [005-desvios-d1-d8](005-desvios-d1-d8.md) | Desvíos de shadcn, CSP, Geist, theme-init y confirmación de Restablecer; el diálogo de archivos ya se usa en 017 | Antes de la 022 y según cada sección | Agente |
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
| [lote-huerfanas-bloqueadas](lote-huerfanos-bloqueadas.md) | 11 carpetas huérfanas y dos temporales; Synapse requiere aprobación puntual | Cuando el usuario lo autorice; no bloquea | Usuario |
| [014-escucha-y-revision](014-escucha-y-revision.md) | Escuchar la narración alineada, revisar la sincronía, la UI real y los presets incluidos (gusto) | Después del merge a dev; no bloquea | Usuario |
| [014-audio-quemar-copia](014-audio-quemar-copia.md) | Al quemar, el audio PCM de un MOV no se ha probado: la copia del audio puede fallar en MP4 | En la verificación final (T9) | Agente |
| [014-traduccion-real](014-traduccion-real.md) | Falta la prueba `-m local` automatizada de la traducción con `small`; la corrida real y el cierre ya están verificados a mano | Después del merge a dev; no bloquea | Agente |
| [014-capturas-editor](014-capturas-editor.md) | Capturas del editor (claro y oscuro) y cuadros de la quema, comparados con `image-reader` (batería 03, puntos 3 y 9) | Después del merge a dev; no bloquea | Agente |
| [015-bitrates-presets](015-bitrates-presets.md) | Los bitrates máximos por plataforma de los presets de redes (D-2) faltan, con sus fuentes | Antes de la verificación final de 015 (T9) | Agente |
| [015-foto-de-prueba](015-foto-de-prueba.md) | La prueba `-m local` de cara real se salta: falta una foto con licencia clara en `server/tests/fixtures/vision/` | Antes de la verificación final de 015 (T9) | Usuario |
| [015-refactor-masterizacion-narracion](015-refactor-masterizacion-narracion.md) | La masterización de la narración repite las dos pasadas de `normalize.py`; migrarla cambia su salida (commit aparte) | Después del merge de 015; no bloquea | Agente |
| [015-repair-primera-instalacion](015-repair-primera-instalacion.md) | `repair` rechaza un motor cuya primera instalación no terminó (`engine_external`); de la spec 009 | Después del merge de 015; no bloquea | Agente |
| [015-trayectoria-y-ab-fuera-de-out](015-trayectoria-y-ab-fuera-de-out.md) | Dibujar la trayectoria de «Seguir a la persona» (con el Editor 017) y el A/B de Normalizar cuando el original está fuera de `out/` y `reference/` | En el e2e de T8 (A/B); la trayectoria, con el Editor | Agente |
| [015-escucha-y-revision](015-escucha-y-revision.md) | Escuchar las normalizaciones, la unión y las convertidas; mirar los encuadres y las capturas; decidir el techo de pico con pérdida y el contraste de la fila de trabajo | Después del merge de 015; no bloquea | Usuario |
| [017-app-check-y-flujo-real](017-app-check-y-flujo-real.md) | Tres corridas compilaron, pero app-check no obtuvo CDP; faltan grabación física, arrastre desde Windows, latencia y capturas | Cuando WebView2 responda a CDP; no bloquea el merge | Agente |
| [017-pytest-temp](017-pytest-temp.md) | Dos temporales de pytest en la raíz del worktree; Synapse bloquea borrarlos sin aprobación manual | Tras aprobación puntual de Synapse, antes de cerrar el worktree | Usuario |
| [021-vision-miniaturas](021-vision-miniaturas.md) | Usar la visión de Gemma 4 para miniaturas o cuadros (fuera de alcance de la 021) | Si el usuario lo pide | Usuario |
| [021-escucha-y-revision](021-escucha-y-revision.md) | Escuchar la narración revisada con el asistente y puntuar sus traducciones | Antes de publicar el lote | Usuario |
| [021-glosario-sobreaplicado](021-glosario-sobreaplicado.md) | «Corregir transcripción» inserta términos del glosario donde no hay error | Con transcripciones reales | Agente y usuario |
| [021-cli-salida-cp1252](021-cli-salida-cp1252.md) | El JSON de `studio` sale en cp1252 cuando la salida va a un pipe | Antes de publicar, o en la 022 | Agente |
| [021-estilo-none-en-txt](021-estilo-none-en-txt.md) | `narration tts --file x.txt` sin `--style` falla con «No existe el estilo None» | Antes de publicar | Agente |
| [021-capitulos-al-reproductor](021-capitulos-al-reproductor.md) | Los capítulos de Publicar se copian, pero no saltan al reproductor del detalle | Con la próxima spec de la Biblioteca; no bloquea el merge | Agente |
| [020-tipos-de-trabajo-en-cola](020-tipos-de-trabajo-en-cola.md) | La cola solo traduce `music` y `narration`; los demás tipos se ven crudos (`library.scan`) | En la 023 o una spec de la cola; no bloquea el merge | Agente |
| [024-aprobar-hooks-codex](024-aprobar-hooks-codex.md) | Aprobar en Codex (`/hooks`) `shell_guard.py` y `computer_use_guard.py`, y probar que bloquea `sky.list_apps()` | Después del merge de 024 y tras cada cambio de un hook | Usuario |
| [024-peaks-403-catalogo](024-peaks-403-catalogo.md) | `/media/peaks` da 403 a las muestras del catálogo de voces (hallado por `app-check`) | Con la próxima spec de voces o `/media` | Agente |
| [022-rutas-largas-hf](022-rutas-largas-hf.md) | La descarga de Hugging Face pasa `MAX_PATH` si la carpeta de motores es muy profunda | Después del lote | Agente |
| [022-firma-de-codigo](022-firma-de-codigo.md) | Firmar el instalador (Azure Trusted Signing, OV o EV): tiene costo | Antes de difundir el instalador | Usuario |
| [016-lufs-real-fuera-de-ac3](016-lufs-real-fuera-de-ac3.md) | Sonoridad de mezclas con picos fuera de AC-3 | Después del merge de 016; no bloquea | Agente |
| [016-escucha-y-capturas](016-escucha-y-capturas.md) | Escucha del usuario, capturas, medición del ducking y corrida de la UI de Mezcla | Después del merge de 016; no bloquea | Agente |
| [016-arrastrar-a-ranura](016-arrastrar-a-ranura.md) | Arrastrar a la ranura y arrastrar regiones de la Mezcla | Después del merge de 016; no bloquea | Agente |
| [023-llm-tildes](023-llm-tildes.md) | El asistente (Qwen3.5-9B) a veces quita tildes y comas al revisar un guion | Antes de publicar; con el próximo ajuste del asistente | Agente |
| [023-transcripcion-por-ruta](023-transcripcion-por-ruta.md) | Publicar busca la transcripción por la ruta escrita igual, no por el archivo | Después del lote | Agente |
| [023-quemar-antes-de-vertical](023-quemar-antes-de-vertical.md) | Quemar subtítulos y después convertir a vertical los corta en los bordes | Con la próxima spec de Convertir o Subtítulos | Agente |
| [023-recorrido-en-la-ui](023-recorrido-en-la-ui.md) | El recorrido encadenado no se hizo con la UI de la app instalada | Antes de publicar la v0.1.0 | Usuario y agente |
| [023-detalles-del-recorrido](023-detalles-del-recorrido.md) | Detalles menores del recorrido: palabra clave con coma y origen viejo en la quema | Después del lote | Agente |
| [022-release-dispatch](022-release-dispatch.md) | AC-10 real: correr `release.yml` en `workflow_dispatch` dry-run cuando esté en `main` | Al pasar el lote a main | Agente |
| [025-pytest-local-candado](025-pytest-local-candado.md) | `gpu-turn run -- pytest -m local` se cuelga con el test de llm, que toma el candado por su cuenta | Agente |
| [025-escucha-salidas](025-escucha-salidas.md) | Escuchar la música y la narración de AC-7 (el espectrograma muestra una caída de energía y un corte de banda en 16 kHz) | Usuario |

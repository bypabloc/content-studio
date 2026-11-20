# Lote 001–021: content-studio como estudio de escritorio

Pedido del usuario (2026-11-18): convertir content-studio en un estudio de escritorio. El código Python pasa a `server/` (FastAPI con SQLite) y toda la UI a `client/` (Tauri 2, React 19, shadcn/ui, Tailwind v4 y oxlint). El código se escribe en inglés, lo valida el cspell de klinikae y el español queda solo en docstrings, comentarios, docs y catálogos. El tema puede ser claro, oscuro o el del sistema. Las secciones son narración, voces, grabación, música, limpiador, subtítulos, conversor, normalizar, recortar y unir, mezcla, editor (NLE) y biblioteca, con iconos en toda la UI. El estudio se distribuye con un instalador NSIS.

Formato: [`plan-format.md`](../../../.agents/rules/plan-format.md). Cada spec es una rama desde `origin/dev` y un PR a `dev`, que se fusionan en orden. La última spec (021) hace la verificación integral y borra esta carpeta.

## Specs

| Spec | Qué | Tipo | Depende de | Estado |
| :--- | :--- | :--- | :--- | :--- |
| [001](001-server-devtools/README.md) | Python a `server/` (uv workspace), datos a `server/data/` y `devtools/` en la raíz | refactor | — | PEN |
| [002](002-english-cspell/README.md) | Código y datos en inglés + cspell de klinikae (spelling en pre-commit y CI) | refactor | 001 | PEN |
| 003 | test-runner en devtools, tests espejo, tamaño, cobertura, docstrings y typecheck | chore | 002 | DON |
| [004](004-server-api/README.md) | Server FastAPI + SQLite (jobs, settings) + cola con turno-gpu + SSE + CLI headless; se borra `cli.py` | feature | 003 | IMP |
| [005](005-client-base/README.md) | Client: Tauri 2, shadcn, catálogo `es.json`, tema light/dark/system, sidebar + cola, selector con estrella, budget, vitest, e2e base | feature | 004 | DON |
| [006](006-narration-section/README.md) | Sección Narración | feature | 005 | PEN |
| [007](007-icons/README.md) | Iconos (lucide-react), `IconButton` con tooltip y criterio de solo icono; sidebar colapsable | feature | 006 | PEN |
| [008](008-voices-recording/README.md) | Voces (catálogo y construir) + Grabar (micrófono en la UI) | feature | 007 | PEN |
| [009](009-music-section/README.md) | Sección Música (duración) | feature | 008 | PEN |
| [010](010-engines-storage/README.md) | Pantalla Motores: instalar venvs y modelos bajo demanda, licencias, ffmpeg del sistema | feature | 009 | PEN |
| [011](011-whisper-cleaner/README.md) | faster-whisper + Limpiador de silencios (audio y video, revisión en línea de tiempo) | feature | 010 | PEN |
| [012](012-subtitles/README.md) | Subtítulos: SRT/VTT, editor, quemar, estilo redes (ASS) | feature | 011 | PEN |
| [013](013-convert-normalize-trim/README.md) | Convertir (audio/video, presets de redes, GIF, extraer audio), normalizar, y los trabajos de recortar, unir y dividir (su pantalla es el Editor) | feature | 012 | PEN |
| [014](014-mix-ducking/README.md) | Mezcla narración + música con ducking | feature | 013 | PEN |
| [015](015-editor-core/README.md) | Editor (núcleo): proyecto, línea de tiempo multipista, explorador de carpetas, importar, grabar, deshacer, imán, marcadores y exportar audio | feature | 014 | PEN |
| [016](016-editor-visual/README.md) | Editor (visual): pistas de video e imagen con alfa, transformar con keyframes, transiciones, vista previa WebGL y exportar video | feature | 015 | PEN |
| [017](017-editor-effects/README.md) | Editor (efectos): texto, velocidad, color y LUT, chroma, fusión, subtítulos y «Abrir en Editor» / «Mandar a…» | feature | 016 | PEN |
| [018](018-library/README.md) | Biblioteca de medios | feature | 017 | PEN |
| [019](019-local-llm-assist/README.md) | Asistente con LLM local (Gemma 4 E4B ★ y Qwen3.5-9B bajo demanda): revisar guion, traducir y corregir subtítulos, caption de música y publicar | feature | 018 | PEN |
| [020](020-installer/README.md) | Instalador NSIS (uv incluido, carpeta de datos elegible, primer arranque) | feature | 019 | PEN |
| [021](021-integral-verification/README.md) | Verificación integral del lote y cierre | chore | 020 | PEN |

Las 21 están redactadas, cada una después de su ronda de preguntas. El 2026-11-19 se sumaron la 007 (iconos) y las 015–017 (editor) y se renumeraron las que no habían empezado (de la 007 en adelante; la 006 conserva su número porque estaba en ejecución), para que el número siga el orden de ejecución. La carpeta conserva el nombre `001-017-studio` para no chocar con el cierre de la 006; la 021 la borra. Se ejecutan con `run-specs` en orden numérico, de la 001 a la 021 (una rama, un worktree y un PR a `dev` por spec).

## Decisiones del usuario que valen para todo el lote

* **Textos**: el código, los identificadores y los strings van en inglés. El texto visible en español vive en `client/messages/es.json` y en un catálogo de mensajes del server. Docs, reglas, specs y `.md` siguen en español y cspell los ignora.
* **Stack**: server con FastAPI, uvicorn y sqlite3 de la stdlib, con migraciones en SQL y `PRAGMA user_version`. Expone HTTP en 127.0.0.1 con OpenAPI, de donde salen los tipos del client. Client con Tauri 2, React 19, TypeScript, Vite, Tailwind v4, shadcn/ui y oxlint.
* **SQLite solo guarda metadatos**: rutas, parámetros, estados de los trabajos, preferencias y cachés (duración, LUFS, picos). **Nunca** audio, video, imágenes ni ningún contenido binario. Los archivos viven en disco y la base solo guarda su ruta. Lo hace cumplir un test de esquema que rechaza columnas `BLOB` (004).
* **Cola**: la tabla `jobs` en SQLite y un worker que toma el turno de la GPU. El progreso llega por SSE. Los trabajos que solo usan ffmpeg pueden correr en paralelo.
* **Preferencias**: cada selector marca con una estrella la opción recomendada y recuerda la última elección del usuario. Se guardan en la tabla `settings`, que también lee el CLI headless.
* **De klinikae**: cspell, `devtools/` en Python, tests espejo, e2e con Playwright, validador de tamaño y budget del client.
* **ffmpeg**: no va dentro del instalador. Se usa el del PATH del sistema. Si falta, la app intenta instalarlo con winget y avisa. Si no puede, le explica al usuario cómo instalarlo y dejarlo accesible.
* **Licencia**: MIT. Los motores no comerciales se ofrecen con una etiqueta y hay que aceptar su licencia para instalarlos.
* **Reglas**: cada spec actualiza las reglas de agentes que deja obsoletas.

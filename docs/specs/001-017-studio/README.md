# Lote 001–023: content-studio como estudio de escritorio

Pedido del usuario (2026-11-18): convertir content-studio en un estudio de escritorio. El código Python pasa a `server/` (FastAPI con SQLite) y toda la UI a `client/` (Tauri 2, React 19, shadcn/ui, Tailwind v4 y oxlint). El código se escribe en inglés, lo valida el cspell de klinikae y el español queda solo en docstrings, comentarios, docs y catálogos. El tema puede ser claro, oscuro o el del sistema. Las secciones son narración, voces, grabación, música, limpiador, subtítulos, conversor, normalizar, recortar y unir, mezcla, editor (NLE) y biblioteca, con iconos en toda la UI. El estudio se distribuye con un instalador NSIS.

Formato: [`plan-format.md`](../../../.agents/rules/plan-format.md). Cada spec es una rama desde `origin/dev` y un PR a `dev`, que se fusionan en orden. La última spec (023) hace la verificación integral y borra esta carpeta.

## Specs

| Spec | Qué | Tipo | Depende de | Estado |
| :--- | :--- | :--- | :--- | :--- |
| 001 | Python a `server/` (uv workspace), datos a `server/data/` y `devtools/` en la raíz | refactor | — | DON |
| 002 | Código y datos en inglés + cspell de klinikae (spelling en pre-commit y CI) | refactor | 001 | DON |
| 003 | test-runner en devtools, tests espejo, tamaño, cobertura, docstrings y typecheck | chore | 002 | DON |
| 004 | Server FastAPI + SQLite (jobs, settings) + cola con turno-gpu + SSE + CLI headless; se borra `cli.py` | feature | 003 | DON |
| [005](005-client-base/README.md) | Client: Tauri 2, shadcn, catálogo `es.json`, tema light/dark/system, sidebar + cola, selector con estrella, budget, vitest, e2e base | feature | 004 | DON |
| [006](006-narration-section/README.md) | Sección Narración | feature | 005 | DON |
| [007](007-i18n/README.md) | Textos centralizados con i18n: un catálogo único (`es`, `en`, `pt`) para el client y el server, idioma en Ajustes y etapa `i18n` que bloquea textos sueltos | feature | 006 | DON |
| [008](008-atomic-components/README.md) | Componentes con Atomic Design: unos 64 componentes de klinikae (`@base-ui/react` + shadcn v4) en `shared/components/{atoms,molecules,organisms}`, `useForm`, tokens, AppShell, y bloqueo de etiquetas HTML nativas fuera de los átomos | refactor · feature | 007 | DON |
| 009 | Iconos aplicados: criterio de solo icono y los iconos del shell, la cola, Narración y Ajustes, con los `UIIcon`, `UIIconButton` y `UITooltip` de la 008 | feature | 008 | DON |
| 010 | Voces (catálogo y construir) + Grabar (micrófono en la UI) | feature | 009 | DON |
| 011 | Sección Música (duración exacta, muestras, comparar y elegir) | feature | 010 | DON |
| [012](012-engines-storage/README.md) | Pantalla Motores: instalar venvs y modelos bajo demanda, licencias, ffmpeg del sistema | feature | 011 | DON |
| [013](013-whisper-cleaner/README.md) | faster-whisper + Limpiador de silencios (audio y video, revisión en línea de tiempo) | feature | 012 | DON |
| [014](014-subtitles/README.md) | Subtítulos: SRT/VTT, editor, quemar, estilo redes (ASS) | feature | 013 | DON |
| [015](015-convert-normalize-trim/README.md) | Convertir (audio/video, presets de redes, GIF, extraer audio), normalizar, y los trabajos de recortar, unir y dividir (su pantalla es el Editor) | feature | 014 | DON |
| [016](016-mix-ducking/README.md) | Mezcla narración + música con ducking | feature | 015 | DON |
| [017](017-editor-core/README.md) | Editor (núcleo): proyecto, línea de tiempo multipista, explorador de carpetas, importar, grabar, deshacer, imán, marcadores y exportar audio | feature | 016 | PEN |
| [018](018-editor-visual/README.md) | Editor (visual): pistas de video e imagen con alfa, transformar con keyframes, transiciones, vista previa WebGL y exportar video | feature | 017 | DON |
| [019](019-editor-effects/README.md) | Editor (efectos): texto, velocidad, color y LUT, chroma, fusión, subtítulos y «Abrir en Editor» / «Mandar a…» | feature | 018 | DON |
| [020](020-library/README.md) | Biblioteca de medios | feature | 019 | DON |
| [021](021-local-llm-assist/README.md) | Asistente con LLM local (Gemma 4 E4B ★ y Qwen3.5-9B bajo demanda): revisar guion, traducir y corregir subtítulos, caption de música y publicar | feature | 020 | PEN |
| [022](022-installer/README.md) | Instalador NSIS (uv incluido, carpeta de datos elegible, primer arranque) | feature | 021 | PEN |
| [023](023-integral-verification/README.md) | Verificación integral del lote y cierre | chore | 022 | PEN |

Las 23 están redactadas, cada una después de su ronda de preguntas. El 2026-11-19 se sumaron, en este orden: la de iconos y las tres del editor; la 007 (i18n); y la 008 (componentes con Atomic Design). Hoy iconos es la 009 y el editor, las 017–019. Las tres veces se renumeraron las que no habían empezado (de la 007 en adelante; la 006 conserva su número porque estaba en ejecución), para que el número siga el orden de ejecución. La carpeta conserva el nombre `001-017-studio` para no chocar con el cierre de la 006; la 023 la borra. Se ejecutan con `run-specs` en orden numérico, de la 001 a la 023 (una rama, un worktree y un PR a `dev` por spec).

## Decisiones del usuario que valen para todo el lote

* **Textos**: el código, los identificadores y los strings van en inglés. Desde la 007, todo texto visible (UI, errores de la API y etiquetas de estilos y motores) vive en un catálogo único, `server/src/content_studio/messages/{es,en,pt}.json`, que usan el client y el server. Cada spec trae sus claves en los tres idiomas, y la etapa `i18n` bloquea los textos sueltos en el código. Docs, reglas, specs y `.md` siguen en español y cspell los ignora.
* **Componentes** (desde la 008): Atomic Design.
  * `client/src/shared/components/` tiene `atoms/`, `molecules/` y `organisms/`, con prefijo `UI` y sobre `@base-ui/react` + shadcn v4.
  * Los templates son `client/src/features/` y las páginas, `client/src/app/`.
  * Las etiquetas HTML nativas solo se permiten en los átomos y en `shared/components/shadcn/`. La etapa `ui-structure` y oxlint lo hacen cumplir, junto con la jerarquía de imports.
* **Stack**: server con FastAPI, uvicorn y sqlite3 de la stdlib, con migraciones en SQL y `PRAGMA user_version`. Expone HTTP en 127.0.0.1 con OpenAPI, de donde salen los tipos del client. Client con Tauri 2, React 19, TypeScript, Vite, Tailwind v4, shadcn/ui y oxlint.
* **SQLite solo guarda metadatos**: rutas, parámetros, estados de los trabajos, preferencias y cachés (duración, LUFS, picos). **Nunca** audio, video, imágenes ni ningún contenido binario. Los archivos viven en disco y la base solo guarda su ruta. Lo hace cumplir un test de esquema que rechaza columnas `BLOB` (004).
* **Cola**: la tabla `jobs` en SQLite y un worker que toma el turno de la GPU. El progreso llega por SSE. Los trabajos que solo usan ffmpeg pueden correr en paralelo.
* **Preferencias**: cada selector marca con una estrella la opción recomendada y recuerda la última elección del usuario. Se guardan en la tabla `settings`, que también lee el CLI headless.
* **De klinikae**: cspell, `devtools/` en Python, tests espejo, e2e con Playwright, validador de tamaño y budget del client.
* **ffmpeg**: no va dentro del instalador. Se usa el del PATH del sistema. Si falta, la app intenta instalarlo con winget y avisa. Si no puede, le explica al usuario cómo instalarlo y dejarlo accesible.
* **Licencia**: MIT. Los motores no comerciales se ofrecen con una etiqueta y hay que aceptar su licencia para instalarlos.
* **Reglas**: cada spec actualiza las reglas de agentes que deja obsoletas.

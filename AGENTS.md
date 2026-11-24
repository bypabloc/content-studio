# content-studio

Audio local para videos en Windows 11 con una RTX 4060 Laptop de 8 GB; nada se corre en WSL. Hay tres herramientas independientes.
El código vive en `server/src/content_studio/`. Sus carpetas de datos guardan docs, voces, catálogos y referencias.
Los venvs y modelos se instalan bajo demanda en la carpeta de motores elegida en Ajustes > Almacenamiento.

| Carpeta | Qué genera | Código | Documentación |
| :--- | :--- | :--- | :--- |
| `server/data/narration/` | Narración TTS en español neutro clonando una voz (Qwen3-TTS, Chatterbox) | `server/src/content_studio/narration/` | [server/data/narration/README.md](server/data/narration/README.md) · [formato del guion](server/data/narration/docs/formato-guion.md) · [grabar voces](server/data/narration/docs/scripts/README.md) |
| `server/data/music/` | Música de fondo instrumental (ACE-Step 1.5, HeartMuLa) | `server/src/content_studio/music/` | [server/data/music/README.md](server/data/music/README.md) · [INVESTIGACION.md](server/data/music/INVESTIGACION.md) |
| — (`studio clean`) | Limpiador de silencios de audio y video, con revisión en línea de tiempo (faster-whisper) | `server/src/content_studio/clean/` | [docs/process/01-done/cleaner.md](docs/process/01-done/cleaner.md) |
| — (`studio convert`, `normalize`, `trim`, `concat`, `split`) | Convertir y normalizar la sonoridad (ffmpeg), y recortar, unir y dividir medios | `server/src/content_studio/media/` | [convert.md](docs/process/01-done/convert.md) · [edit.md](docs/process/01-done/edit.md) |
| — (`studio editor render`) | Editor no destructivo: títulos, velocidad, color/LUT, chroma, fusión, subtítulos, keyframes y exportación | `server/src/content_studio/editor/` · `client/src/features/editor/` | [editor.md](docs/process/01-done/editor.md) |

**Antes de usar cualquiera de las dos, lee su README**: ahí están el uso, los flags, el rendimiento medido, los tips y los problemas conocidos.

## Atajos

Todo se lanza desde `studio`, el CLI headless (argparse): `uv run studio <comando> [flags]`. No hay menú ni asistente: ningún comando pregunta nada, con o sin TTY.

`narration tts` y `music` encolan el trabajo en `var/content-studio.db` y lo corren en su proceso; `serve` corre los que quedan en la cola. Cada trabajo sale en `out/<tipo>/<AAAA-MM-DD>-<id>-<slug>/` con `params.json`, y su log en `logs/jobs/<id>.log`. `studio` no acepta `--output` ni `--folder`; `--db RUTA` va antes o después del subcomando.

```bash
uv run studio --help                         # subcomandos; cada uno tiene --help con sus flags
uv run studio narration tts --model qwen-0.6b --style expert --voice yesid --text "..."   # → out/narration/
uv run studio narration voices --build all   # voces libres aprobadas en los 12 estilos
uv run studio music --model acestep --style lofi-chill corporate --duration 30            # → out/music/
uv run studio serve --port 8000 --token T    # API en 127.0.0.1 con el worker de la cola
uv run studio jobs list --kind music         # también: jobs cancel ID y jobs retry ID
uv run studio library list --kind music      # también: library scan --add DIR, tag ID NOMBRE y trash RUTA
uv run studio convert charla.wav --target mp3 --option vbr=2   # → out/media/ (también normalize, trim, concat, split)
```

**Client** (la app de escritorio, en `client/`, con Tauri): `bun run --cwd client tauri dev` abre «Content Studio» y levanta el server solo; `bun run --cwd client build` y `test` compilan y prueban. Reglas: [frontend-stack](.agents/rules/frontend-stack.md) y [ui-components](.agents/rules/ui-components.md).

`studio` es el script de `server/pyproject.toml`. Los motores se relanzan solos en el venv de cada uno (`common/process.py`); `studio engines` lista, instala, verifica, repara y desinstala motores. Las recetas fijan paquetes, versiones y revisiones. Los módulos directos siguen con `PYTHONPATH=server/src python -m content_studio.narration.tts ...`.

## Arquitectura

```
server/src/content_studio/
├── paths.py                  ROOT, data_dir(), engines_dir(), outputs_dir(), db_path()…
├── messages.py               catálogo de textos (messages/{es,en,pt}.json) e idioma de Accept-Language
├── common/                   process (relaunch en un venv, use_venv), ffmpeg, files
├── cli/                      argparse de `studio`: main (subcomandos), submit (encola), serve (API y worker)
├── services/                 un servicio por tipo de trabajo (narration, music); registry.py con SERVICES
├── jobs/                     cola y worker: queue, runner, worker
├── api/                      FastAPI y uvicorn: app, events (SSE), routes/, token Bearer
├── db/                       SQLite (stdlib) en WAL con migraciones SQL: connection, schema, jobs, settings
├── narration/                parser (liviano), tts (main), styles, blocks, pipeline, audio, script, metadata, reference
│   ├── engines/              EngineSpec + TTSEngine (Factory Method) y registry.py con ENGINES
│   ├── text/ evaluation/     segments y translate por motor; compare y review (whisper)
│   └── voices/               catálogo de voces libres: catalog, sources, build, main
├── music/                    parser (liviano), music_main (main), styles, evaluation
    └── engines/              MusicSpec + MusicEngine y registry.py con MODELS
├── engines/                  recetas versionadas, instalación y mantenimiento de venvs/modelos
├── library/                  biblioteca: índice, carpetas vigiladas, búsqueda, acciones y espacio
├── storage/                  reubicación segura de motores y salidas
└── system/                   detección e instalación de FFmpeg/Git y detección de GPU
```

Dos capas: los `parser.py`, los catálogos y `cli/` solo importan stdlib; torch, numpy y los motores se importan dentro de las funciones, así `--help` no necesita sus venvs.

- **Agregar un motor TTS o de música**: un archivo en `engines/`, una entrada en `engines/registry.py`, una receta fijada en `server/src/content_studio/engines/recipes/` y su librería en `LIBRARIES` (`server/tests/integration/test_venvs.py`).
- **Agregar un servicio** (un tipo de trabajo): un módulo en `services/` con `RESOURCE`, `validate(params)` y `build_command(params, out_dir)`, y una línea en `SERVICES`. La API y `studio` lo usan solos.
- **Tamaño por categoría**: fuente 300 líneas, tests 800 (`test-runner --type=validators`); Python 3.10 como mínimo. Detalle en [codigo-python](.agents/rules/codigo-python.md).

## Forma de trabajo y dónde buscar

`AGENTS.md` y `.agents/` son las instrucciones compartidas de todos los agentes (Claude Code, Codex, Antigravity). `.claude/` tiene las mismas reglas y skills con el frontmatter de Claude Code (`python -m devtools rules --sync`), más sus hooks, agentes, comandos y el plugin `session-handoff`; no vincula a otros agentes.

| Necesidad | Fuente |
| :--- | :--- |
| Código, capas, tamaño, cómo agregar un motor o un servicio | [codigo-python](.agents/rules/codigo-python.md), [stack](.agents/rules/stack.md) |
| Git, ramas, PR, hooks locales | [git-workflow](.agents/rules/git-workflow.md) |
| Diseñar una spec (plantillas en [docs/specs/_plantilla/](docs/specs/_plantilla/README.md)) | [plan-format](.agents/rules/plan-format.md); skills `crear-spec`, `execute-spec`, `run-specs` |
| Estado del proyecto, roadmap, decisiones y pendientes | [docs/process/](docs/process/README.md), [project-progress](.agents/rules/project-progress.md) |
| Tests y TDD | [testing](.agents/rules/testing.md); skills `tdd-workflow`, `testing` |
| Verificar antes de decir "listo" (duración, volumen, espectrograma) | [verify-before-claiming-done](.agents/rules/verify-before-claiming-done.md) |
| Dónde va la salida de cada comando | [command-output](.agents/rules/command-output.md) |
| Sesiones largas y seguir hasta terminar | Plugin [session-handoff](https://github.com/bypabloc/claude-plugin-session-handoff) (solo Claude Code), configurado en `.claude/session-handoff.json` |
| Frontend del client (Tauri, React, textos, componentes) | [frontend-stack](.agents/rules/frontend-stack.md), [ui-components](.agents/rules/ui-components.md) |
| Varias sesiones: worktrees y turno de la GPU | [worktrees](.agents/rules/worktrees.md), [gpu-turn](.agents/rules/turno-gpu.md), [agentes-y-tokens](.agents/rules/agentes-y-tokens.md) |
| Buscar código | [graphify](.agents/rules/graphify.md); skills `graphify-query`, `graphify-ops` |
| devtools del flujo de agentes (`devtools/`, en la raíz) | [devtools](.agents/rules/devtools.md) |
| Idioma del código, del CLI y de la narración | [textos-e-idioma](.agents/rules/textos-e-idioma.md) |
| Cambiar reglas, skills o hooks de agentes | [agent-config-testing](.agents/rules/agent-config-testing.md) |

## Pruebas

```bash
python -m devtools test-runner --type=all   # lo que corre CI (sin GPU)
uv run pytest            # doctests y bugs (sin GPU)
uv run pytest -m local   # además, cada venv de motor importa su librería (solo en este equipo)
python -m devtools test-runner --type=e2e   # Playwright sobre la app construida (Chromium; en la CI, el job client)
```

## Reglas

1. **Salidas** en `out/` (cada trabajo en su carpeta `<AAAA-MM-DD>-<id>-<slug>/`, con `params.json`) y **logs** en `logs/`. Ambas están gitignoreadas y no se limpian. Las corridas largas (HeartMuLa tarda ~5 min por pista) van en segundo plano, con la salida en `logs/`.
2. **Un modelo a la vez en la GPU.** Narración y música juntas no caben en 8 GB. Entre sesiones, con `gpu-turn run` ([turno-gpu](.agents/rules/turno-gpu.md)); `studio` y el worker toman el candado solos.
3. **La música es siempre instrumental**: nada de voz ni de letra.
4. **Verificar antes de decir "listo"**: correr el script real y revisar la duración, el volumen y el espectrograma (ver los README). La UI se verifica con `python -m devtools app-check run`; **Computer Use está prohibido** y lo bloquea un hook. El gusto lo decide el usuario: entrégale las rutas.
5. **Licencias**: VoxCPM2, Qwen3-TTS y HeartMuLa (Apache 2.0), y Chatterbox y ACE-Step (MIT) permiten uso comercial. CosyVoice 3 es Apache 2.0, pero su tarjeta dice "academic purposes": revísalo antes de un uso comercial.
   OmniVoice (CC-BY-NC) e IndexTTS (bilibili Model Use License) **no** son comerciales. La lista vigente está en `server/src/content_studio/narration/engines/registry.py`. Clona solo voces con permiso de su dueño.
6. Idioma de trabajo: español, en respuestas concisas y sin adulación. Narración en español neutro latinoamericano, salvo que se pida otro idioma.
7. Los archivos se crean y editan con las herramientas de edición del agente. Bash se usa solo para ejecutar los scripts y ffmpeg. Muestra los resultados con rutas clicables a `out/`.
8. **YAGNI**: escribe solo lo que la tarea pide y prefiere la solución de una línea que se entienda de un vistazo. Nada de abstracciones, opciones ni código "por si acaso"; nunca recortes validación, manejo de errores ni seguridad ([plan-format](.agents/rules/plan-format.md) §0).

## Requisitos

`uv`, `bun` (para el client) y Rust con `cargo` (para Tauri) son requisitos de desarrollo.
FFmpeg y Git se detectan en el PATH; en Windows, la app puede ofrecer instalarlos con winget.
Los motores que requieren GPU necesitan una NVIDIA compatible; los motores aptos para CPU siguen disponibles sin ella.
Los venvs y modelos usan `%LOCALAPPDATA%\Content Studio\engines` por defecto en Windows.
La ruta se puede cambiar desde Ajustes > Almacenamiento.
Para los agentes, una vez por clon: `git config core.hooksPath .git-hooks` y `uv tool install graphifyy && graphify update .` (skill `graphify-ops`).

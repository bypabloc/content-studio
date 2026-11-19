# content-studio

Audio local para videos, en una RTX 4060 Laptop (8 GB) con WSL2. Hay dos herramientas independientes. El código de las dos vive en `server/src/content_studio/`; sus carpetas (`server/data/narration/`, `server/data/music/`) guardan solo datos: docs, voces, catálogo, venvs y modelos.

| Carpeta | Qué genera | Código | Documentación |
| :--- | :--- | :--- | :--- |
| `server/data/narration/` | Narración TTS en español neutro clonando una voz (Qwen3-TTS, Chatterbox) | `server/src/content_studio/narration/` | [server/data/narration/README.md](server/data/narration/README.md) · [formato del guion](server/data/narration/docs/formato-guion.md) · [grabar voces](server/data/narration/docs/scripts/README.md) |
| `server/data/music/` | Música de fondo instrumental (ACE-Step 1.5, HeartMuLa) | `server/src/content_studio/music/` | [server/data/music/README.md](server/data/music/README.md) · [INVESTIGACION.md](server/data/music/INVESTIGACION.md) |

**Antes de usar cualquiera de las dos, lee su README**: ahí están el uso, los flags, el rendimiento medido, los tips y los problemas conocidos.

## Atajos

Todo se lanza desde `cli.py`, hecho con [Typer](https://typer.tiangolo.com), [Rich](https://rich.readthedocs.io) y [questionary](https://questionary.readthedocs.io): `python cli.py <herramienta> <comando> [flags]`.

- **Sin argumentos** abre un menú con flechas que muestra la VRAM libre y cuántas voces de referencia hay grabadas.
- **Si falta un flag obligatorio o uno es inválido**, el asistente lo pide: listas con descripción (licencia, VRAM y si está instalado cada motor), casillas con filtro para los 126 estilos de música, rutas con Tab y números validados. Después muestra un resumen editable, con los valores por defecto en gris y el comando equivalente, para ejecutar, cambiar o agregar cualquier flag.
- **Con todos los flags**, se ejecuta directo. **Sin TTY** (agentes, scripts, `| cat`), no pregunta nada y se comporta como el script.

```bash
python cli.py                            # menú
python cli.py narration tts              # asistente
python cli.py narration tts --help       # ayuda en tabla: flags, valores, defecto y obligatorios

# Narración (sin grabaciones propias todavía: una voz libre del catálogo con consentimiento)
python cli.py narration tts --model qwen-0.6b --style expert \
  --voice yesid --text "..."                                       # → out/narration/

# Grabar las voces de referencia
python cli.py narration grabar --list

# Voces libres (CC0 o dominio público), aprobadas en los 12 estilos: construir y narrar con una
python cli.py narration voices --build all
python cli.py narration tts --model cosyvoice3 --voice yesid --text "..."

# Música (presets con tonalidad/BPM/compás definidos; texto libre exige --key y --bpm)
python cli.py music --model acestep --style lofi-chill corporate --duration 30   # → out/music/
```

`cli.py` funciona con cualquier `python`: si no tiene las dependencias, se relanza con `uv run --script` (están en su cabecera PEP 723). Cada comando, a su vez, se relanza solo en el venv de su motor. También se puede llamar un módulo directo: `PYTHONPATH=server/src python -m content_studio.narration.tts ...` (o `content_studio.music.music_main`, `content_studio.narration.voices.main`), y `uv run content-studio` es lo mismo que `python cli.py`. `grabar` necesita rich y questionary: directo, con `uv run python -m content_studio.narration.grabar.main`.

## Arquitectura

```
cli.py                        shim: relanza con uv si faltan typer/rich/questionary y llama a content_studio.cli.app
server/src/content_studio/
├── paths.py                  ROOT, OUT, LOGS, NARRATION, MUSIC, REFERENCE, VOICES…
├── common/                   process (relaunch en un venv, use_venv), ffmpeg, files
├── cli/                      Typer: app, menu, flow (asistente), widgets, args, help_text; commands/ con Comando y REGISTRY
├── devtools/                 flujo de agentes: worktree, gpu-turn, agent-context, rules (python -m devtools)
├── narration/                parser (liviano), tts (main), styles, blocks, pipeline, audio, script, metadata, reference
│   ├── engines/              EngineSpec + TTSEngine (Factory Method) y registry.py con ENGINES
│   ├── text/ evaluation/     segments y translate por motor; compare y review (whisper)
│   ├── voices/               catálogo de voces libres: catalog, sources, build, main
│   └── grabar/               grabar referencias: kit, dispositivos, interfaz, toma, main
└── music/                    parser (liviano), music_main (main), styles, evaluation
    └── engines/              MusicSpec + MusicEngine y registry.py con MODELS
```

Dos capas: los `parser.py`, los catálogos y el CLI solo importan stdlib (y typer/rich/questionary en `cli/` y `grabar/`), así `--help` y el asistente funcionan sin los venvs. torch, numpy y las librerías de cada motor se importan dentro de las funciones, ya en el venv del motor.

- **Agregar un motor TTS o de música**: un archivo en `engines/` con su subclase de `TTSEngine` o `MusicEngine`, una entrada `EngineSpec`/`MusicSpec` en `engines/registry.py` (venv, módulo, clase, licencia) y su venv. El parser y el asistente lo toman del registro; en `server/tests/test_venvs.py` se agrega la librería que importa (`LIBRARIES`).
- **Agregar un comando del CLI**: una subclase de `Comando` en `cli/commands/` (clave, módulo, parser liviano con `construir_parser()`) y una línea en `REGISTRY` (`cli/commands/__init__.py`).
- **Máximo 300 líneas por `.py`** (lo comprueba `tests/validators/test_structure.py`) y Python 3.10 como mínimo. Detalle en [codigo-python](.agents/rules/codigo-python.md).

## Forma de trabajo y dónde buscar

`AGENTS.md` y `.agents/` (reglas y skills) son las instrucciones compartidas de todos los agentes (Claude Code, Codex, Antigravity). `.claude/` tiene las mismas reglas y skills con el frontmatter de Claude Code (las sincroniza `python -m devtools rules --sync`), más su configuración propia: hooks, agentes `code-explorer`, `researcher` e `image-reader` (Haiku), comandos y el plugin `session-handoff`. Lo de `.claude/` no vincula a otros agentes.

| Necesidad | Fuente |
| :--- | :--- |
| Código, capas, 300 líneas, cómo agregar un motor o comando | [codigo-python](.agents/rules/codigo-python.md), [stack](.agents/rules/stack.md) |
| Git, ramas, PR, hooks locales | [git-workflow](.agents/rules/git-workflow.md) |
| Diseñar una spec (plantillas en [docs/specs/_plantilla/](docs/specs/_plantilla/README.md)) | [plan-format](.agents/rules/plan-format.md); skills `crear-spec`, `execute-spec`, `run-specs` |
| Estado del proyecto, roadmap, decisiones y pendientes | [docs/process/](docs/process/README.md), [project-progress](.agents/rules/project-progress.md) |
| Tests y TDD | [testing](.agents/rules/testing.md); skills `tdd-workflow`, `testing` |
| Verificar antes de decir "listo" (duración, volumen, espectrograma) | [verify-before-claiming-done](.agents/rules/verify-before-claiming-done.md) |
| Dónde va la salida de cada comando | [command-output](.agents/rules/command-output.md) |
| Sesiones largas: handoff en disco y seguir hasta terminar | Plugin [session-handoff](https://github.com/bypabloc/claude-plugin-session-handoff) (solo Claude Code), configurado en `.claude/session-handoff.json` |
| Varias sesiones: worktrees y turno de la GPU | [worktrees](.agents/rules/worktrees.md), [gpu-turn](.agents/rules/turno-gpu.md), [agentes-y-tokens](.agents/rules/agentes-y-tokens.md) |
| Buscar código | [graphify](.agents/rules/graphify.md); skills `graphify-query`, `graphify-ops` |
| devtools del flujo de agentes | [devtools](.agents/rules/devtools.md) |
| Idioma del código, del CLI y de la narración | [textos-e-idioma](.agents/rules/textos-e-idioma.md) |
| Cambiar reglas, skills o hooks de agentes | [agent-config-testing](.agents/rules/agent-config-testing.md) |

## Pruebas

```bash
uv run ruff check && uv run ruff format --check
uv run pytest            # doctests, caracterización, estructura, CLI y bugs (sin GPU; lo mismo corre en CI)
uv run pytest -m local   # además, cada venv de motor importa su librería (solo en este equipo)
```

## Reglas

1. **Salidas** en `out/narration/` y `out/music/`, o donde indiquen `--output` (narration) y `--folder` (music). **Logs** en `logs/<herramienta>-<descripción>.log`. Las dos carpetas están gitignoreadas y no se limpian. Las corridas largas (HeartMuLa tarda ~5 min por pista) se lanzan en segundo plano, con la salida en `logs/`.
2. **Un modelo a la vez en la GPU.** Narración y música juntas no caben en 8 GB. Si la VRAM se desborda a la RAM compartida de WSL, todo va ~4× más lento. Entre sesiones, con `gpu-turn run` ([gpu-turn](.agents/rules/turno-gpu.md)).
3. **La música es siempre instrumental**: nada de voz ni de letra.
4. **Verificar antes de decir "listo"**: correr el script real y revisar la duración, el volumen y el espectrograma (ver los README). El gusto lo decide el usuario: entrégale las rutas.
5. **Licencias**: VoxCPM2, Qwen3-TTS y HeartMuLa (Apache 2.0), y Chatterbox y ACE-Step (MIT) permiten uso comercial. CosyVoice 3 es Apache 2.0, pero su tarjeta dice "academic purposes": revísalo antes de un uso comercial. OmniVoice (CC-BY-NC) e IndexTTS (bilibili Model Use License) **no** son comerciales. La lista vigente está en `server/src/content_studio/narration/engines/registry.py`. Clona solo voces con permiso de su dueño.
6. Idioma de trabajo: español, en respuestas concisas y sin adulación. Narración en español neutro latinoamericano, salvo que se pida otro idioma.
7. Los archivos se crean y editan con las herramientas de edición del agente. Bash se usa solo para ejecutar los scripts y ffmpeg. Muestra los resultados con rutas clicables a `out/`.

## Requisitos

`ffmpeg`, `uv` y GPU NVIDIA. La instalación de cada herramienta está en su README. Para los agentes, una vez por clon: `git config core.hooksPath .git-hooks` y `uv tool install graphifyy && graphify update .` (skill `graphify-ops`).

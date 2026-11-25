---
paths:
  - "server/src/**"
  - "pyproject.toml"
  - "server/data/narration/**"
  - "server/data/music/**"
---

# Stack: Python, uv, motores con recetas, ffmpeg

## 1. Piezas y su rol

| Pieza | Rol | Dónde |
| :--- | :--- | :--- |
| Python 3.15 (`.python-version`); piso de los motores desde sus recetas (hoy 3.10) | Server, devtools y CI en 3.15 (la CI solo corre en PR ajenos); el código de `narration/` y `music/` que corre en los venvs de los motores, en el piso (CosyVoice y HeartMuLa) | `server/src/content_studio/`, `devtools/python_floor.py` |
| uv | Venv de desarrollo (`uv sync`), `uv run ruff/pytest` y el CLI `uv run studio <comando>` | `pyproject.toml`, `uv.lock` |
| argparse | CLI `studio` (`serve`, `narration`, `music`, `jobs`), solo stdlib | `server/src/content_studio/cli/` |
| FastAPI + uvicorn | API local en 127.0.0.1 con token Bearer y `/events` por SSE; `studio serve` la levanta junto con el worker de la cola | `server/src/content_studio/api/` |
| sqlite3 (stdlib) en WAL | Base de trabajos (`var/content-studio.db`) con migraciones en SQL según `PRAGMA user_version` | `server/src/content_studio/db/` |
| Un venv por motor | torch, numpy y la librería del motor, aislados; el comando se relanza en su venv (`common/process.use_venv`) | `paths.engines_dir()` |
| Motores TTS | VoxCPM2, Qwen3-TTS, Chatterbox, CosyVoice 3, OmniVoice, IndexTTS (licencias en `AGENTS.md` y `registry.py`) | `server/src/content_studio/narration/engines/registry.py` (`ENGINES`) |
| Motores de música | ACE-Step 1.5, HeartMuLa | `server/src/content_studio/music/engines/registry.py` (`MODELS`) |
| Recetas de instalación | Pasos y revisiones fijados por motor; instalación reanudable | `server/src/content_studio/engines/recipes/` |
| llama.cpp (`llama-server`, CUDA de Windows) | Asistente local: un proceso hijo con API compatible con OpenAI y JSON schema, bajo demanda y con el turno de la GPU (spec 021) | `server/src/content_studio/llm/`, receta `llama-cpp` |
| ffmpeg / ffprobe | Conversión, loudnorm, recortes, espectrogramas y medición; FFmpeg se detecta en PATH | `common/ffmpeg` |
| Git y FFmpeg | Detección por PATH; en Windows la app puede ofrecer instalación con `winget --scope user` | `server/src/content_studio/system/tools.py` |
| whisper | Comparar y revisar la narración contra el guion | `server/data/narration/evaluation/` |
| ruff + pytest | Lint (`ANN001/ANN201`, comillas simples, 120 columnas) y pruebas con doctests | `pyproject.toml` |

## 2. Equipo

* RTX 4060 Laptop de 8 GB, Windows 11. Todo se corre y se prueba desde Windows (`D:\…`); WSL no se usa (`command-output.md`). La CI corre en Linux.
* Un modelo a la vez en la GPU (`turno-gpu.md`). Si la VRAM desborda a la RAM compartida, todo va ~4× más lento.
* En Windows, `python3` es el stub de la Store: los hooks y scripts usan `uv run --no-project python` o `python`.

## 3. Dos capas

En el nivel superior de un módulo solo va stdlib (salvo `api/`, con fastapi y uvicorn); torch, numpy, soundfile y cada motor se importan dentro de funciones. Así `studio --help`, los parsers y el catálogo funcionan sin los venvs (`codigo-python.md`).

## 4. Motores y almacenamiento

`paths.engines_dir()` devuelve `storage.engines` o `%LOCALAPPDATA%\Content Studio\engines` en Windows.
En POSIX usa `~/.local/share/content-studio/engines`; `paths.models_cache()` apunta a `engines_dir()/hf`.
Ajustes > Almacenamiento permite elegir y reubicar las carpetas de motores y salidas con verificación.
Las referencias, voces y demás datos versionados siguen en `server/data/`.
En modo dev, las instalaciones manuales se detectan como externas y no se desinstalan ni mueven sin confirmación explícita.

## 5. Fuera del stack sin decisión

Servicios web o APIs pagas (TTS o música en la nube), Docker, bases de datos distintas de SQLite (la de la stdlib sí está), Typer (la CLI es argparse), Poetry/pip-tools/conda para el proyecto, notebooks, frameworks de configuración. Si una opción los requiere, va como decisión en una spec, con su ficha en `docs/process/WARNING/`.

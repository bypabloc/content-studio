---
trigger: model_decision
description: Stack de content-studio (Python 3.10+, uv, argparse, FastAPI y uvicorn, SQLite en WAL, un venv por motor, ffmpeg, Windows; nada en WSL) y qué queda fuera sin decisión
---

# Stack: Python, uv, un venv por motor, ffmpeg

## 1. Piezas y su rol

| Pieza | Rol | Dónde |
| :--- | :--- | :--- |
| Python ≥ 3.10 (CI en 3.10 y 3.12) | Todo el código; 3.10 por el venv de CosyVoice | `server/src/content_studio/` |
| uv | Venv de desarrollo (`uv sync`), `uv run ruff/pytest`, el CLI `uv run studio <comando>` y el grupo `legacy` de `grabar/` (`uv run --group legacy ...`) | `pyproject.toml`, `uv.lock` |
| argparse | CLI `studio` (`serve`, `narration`, `music`, `jobs`), solo stdlib | `server/src/content_studio/cli/` |
| FastAPI + uvicorn | API local en 127.0.0.1 con token Bearer y `/events` por SSE; `studio serve` la levanta junto con el worker de la cola | `server/src/content_studio/api/` |
| sqlite3 (stdlib) en WAL | Base de trabajos (`var/content-studio.db`) con migraciones en SQL según `PRAGMA user_version` | `server/src/content_studio/db/` |
| Rich + questionary | Solo el grupo `legacy`, para `grabar/` | `server/src/content_studio/narration/grabar/` |
| Un venv por motor | torch, numpy y la librería de cada motor, aislados; el comando se relanza solo en el suyo (`common/process.use_venv`) | `server/data/narration/.venv-*`, `server/data/music/.venv-*`, `server/data/narration/engines/*/.venv` |
| Motores TTS | VoxCPM2, Qwen3-TTS, Chatterbox, CosyVoice 3, OmniVoice, IndexTTS (licencias en `AGENTS.md` y `registry.py`) | `server/data/narration/engines/registry.py` (`ENGINES`) |
| Motores de música | ACE-Step 1.5, HeartMuLa | `server/data/music/engines/registry.py` (`MODELS`) |
| ffmpeg / ffprobe | Conversión, loudnorm, recortes, espectrogramas y medición | `common/ffmpeg` |
| whisper | Comparar y revisar la narración contra el guion | `server/data/narration/evaluation/` |
| ruff + pytest | Lint (`ANN001/ANN201`, comillas simples, 120 columnas) y pruebas con doctests | `pyproject.toml` |

## 2. Equipo

* RTX 4060 Laptop de 8 GB, Windows 11. Todo se corre y se prueba desde Windows (`D:\…`); WSL no se usa (`command-output.md`). La CI corre en Linux.
* Un modelo a la vez en la GPU (`turno-gpu.md`). Si la VRAM desborda a la RAM compartida, todo va ~4× más lento.
* En Windows, `python3` es el stub de la Store: los hooks y scripts usan `uv run --no-project python` o `python`.

## 3. Dos capas

En el nivel superior de un módulo solo va stdlib (salvo `api/`, con fastapi y uvicorn, y `grabar/`, con rich y questionary); torch, numpy, soundfile y cada motor se importan dentro de funciones. Así `studio --help`, los parsers y el catálogo funcionan sin los venvs (`codigo-python.md`).

## 4. Fuera del stack sin decisión

Servicios web o APIs pagas (TTS o música en la nube), Docker, bases de datos distintas de SQLite (la de la stdlib sí está), Typer (la CLI es argparse), Poetry/pip-tools/conda para el proyecto, notebooks, frameworks de configuración. Si una opción los requiere, va como decisión en una spec, con su ficha en `docs/process/WARNING/`.

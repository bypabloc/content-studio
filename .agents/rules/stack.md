---
trigger: model_decision
description: Stack de content-studio (Python 3.10+, uv, Typer/Rich/questionary, un venv por motor, ffmpeg, Windows y WSL2) y qué queda fuera sin decisión
---

# Stack: Python, uv, un venv por motor, ffmpeg

## 1. Piezas y su rol

| Pieza | Rol | Dónde |
| :--- | :--- | :--- |
| Python ≥ 3.10 (CI en 3.10 y 3.12) | Todo el código; 3.10 por el venv de CosyVoice | `src/content_studio/` |
| uv | Venv de desarrollo (`uv sync`), `uv run ruff/pytest`, y relanzar `cli.py` con su cabecera PEP 723 si faltan dependencias | `pyproject.toml`, `uv.lock` |
| Typer + Rich + questionary | CLI, menú con flechas, asistente y tablas; solo en `cli/` y `grabar/` | `src/content_studio/cli/` |
| Un venv por motor | torch, numpy y la librería de cada motor, aislados; el comando se relanza solo en el suyo (`comun/proceso.usar_venv`) | `narration/.venv-*`, `music/.venv-*`, `narration/motores/*/.venv` |
| Motores TTS | VoxCPM2, Qwen3-TTS, Chatterbox, CosyVoice 3, OmniVoice, IndexTTS (licencias en `AGENTS.md` y `registro.py`) | `narration/motores/registro.py` (`MOTORES`) |
| Motores de música | ACE-Step 1.5, HeartMuLa | `music/motores/registro.py` (`MODELOS`) |
| ffmpeg / ffprobe | Conversión, loudnorm, recortes, espectrogramas y medición | `comun/ffmpeg` |
| whisper | Comparar y revisar la narración contra el guion | `narration/evaluacion/` |
| ruff + pytest | Lint (`ANN001/ANN201`, comillas simples, 120 columnas) y pruebas con doctests | `pyproject.toml` |

## 2. Equipo

* RTX 4060 Laptop de 8 GB, Windows 11 con WSL2. La misma carpeta del repo se usa desde Windows (`D:\…`) y desde WSL (`/mnt/d/…`): los venvs de los motores son del sistema donde se crearon.
* Un modelo a la vez en la GPU (`turno-gpu.md`). Si la VRAM desborda a la RAM compartida, todo va ~4× más lento.
* En Windows, `python3` es el stub de la Store: los hooks y scripts usan `uv run --no-project python` o `python`.

## 3. Dos capas

En el nivel superior de un módulo solo va stdlib (salvo `cli/` y `grabar/`); torch, numpy, soundfile y cada motor se importan dentro de funciones. Así `--help`, los parsers, el catálogo y el asistente funcionan sin los venvs (`codigo-python.md`).

## 4. Fuera del stack sin decisión

Servicios web o APIs pagas (TTS o música en la nube), Docker, bases de datos, Poetry/pip-tools/conda para el proyecto, notebooks, frameworks de configuración. Si una opción los requiere, va como decisión en una spec, con su ficha en `docs/process/WARNING/`.

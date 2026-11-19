# Verificar antes de decir "listo" — SIEMPRE ACTIVA

**Nunca** reportes "listo", "funciona" o "aplicado" sobre un cambio ejecutable sin haber corrido ese código (o su suite) e inspeccionado el resultado real. Los tests con mocks no bastan cuando el cambio afecta un audio, el formato de un archivo de salida o lo que ve el usuario en el CLI.

## 1. Qué correr según lo que tocaste

| Área | Verificación |
| :--- | :--- |
| Cualquier `.py` | `uv run ruff check && uv run ruff format --check && uv run pytest` |
| Un motor o su registro | `uv run pytest -m local` y una corrida real corta con `gpu-turn run` |
| Narración o música | La corrida real (con `gpu-turn run`) y la medición de §2 de cada salida |
| CLI o asistente | `python cli.py <comando> --help`, un caso real y uno de error; sin TTY (`| cat`) no debe preguntar nada |
| devtools | `python -m devtools <comando> --help`, un caso real y uno de error |
| Hooks o configuración de agentes | `uv run pytest .claude/hooks/tests/test_hooks.py .agents/hooks` y la validación headless (`agent-config-testing.md`) |

## 2. Medir el audio

```bash
ffprobe -v error -show_entries format=duration -of csv=p=0 out/music/<archivo>.wav            # duración
ffmpeg -i out/music/<archivo>.wav -af ebur128 -f null - 2>&1 | tail -12                       # LUFS integrado y pico
ffmpeg -y -i out/music/<archivo>.wav -lavfi showspectrumpic=s=800x300 tmp/verificar/spec.png  # espectrograma
```

* La duración coincide con la pedida; el volumen está en el rango del README (sin clipping); el espectrograma no muestra cortes, silencios inesperados ni, en música, formantes de voz.
* El espectrograma lo abre el agente `image-reader` (Haiku), nunca la ventana principal: el hook `image_read_guard.py` lo bloquea.
* **El gusto lo decide el usuario**: entrégale las rutas clicables de `out/`. "Suena bien" no se afirma sin que lo escuche.

## 3. Transparencia

Si algo no se pudo correr (falta un venv, la GPU está ocupada por otra sesión, no hay credenciales), dilo explícitamente: *"Pasaron ruff y pytest; la corrida real con Qwen queda pendiente porque falta `server/data/narration/.venv-qwen`."* Nunca asumas que funciona porque no hay errores de sintaxis.

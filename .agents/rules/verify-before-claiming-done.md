---
trigger: always_on
description: Nunca reportar "listo" sin correr el código real y medir la salida (duración, volumen, espectrograma); transparencia cuando no se pudo
---

# Verificar antes de decir "listo" — SIEMPRE ACTIVA

**Nunca** reportes "listo", "funciona" o "aplicado" sobre un cambio ejecutable sin haber corrido ese código (o su suite) e inspeccionado el resultado real. Los tests con mocks no bastan cuando el cambio afecta un audio, el formato de un archivo de salida o lo que ve el usuario en el CLI.

## 1. Qué correr según lo que tocaste

| Área | Verificación |
| :--- | :--- |
| Cualquier `.py` | `uv run ruff check && uv run ruff format --check && uv run pytest` |
| Un motor o su registro | `uv run pytest -m local` y una corrida real corta con `gpu-turn run` |
| Narración o música | La corrida real con `uv run studio narration tts` o `music` (toman el candado solos; `turno-gpu.md`) y la medición de §2 de cada salida |
| CLI studio | `uv run studio <comando> --help`, un caso real y uno de error; sin TTY (`| cat`) no debe preguntar nada |
| API o cola | `uv run pytest server/tests/unit/src/content_studio/api server/tests/unit/src/content_studio/jobs`, y un trabajo real con `uv run studio narration tts` o `music`; studio toma el candado solo, así que no lo envuelvas en `gpu-turn run` (`turno-gpu.md`) |
| La UI del client (una pantalla, un flujo, el tema) | `bun run --cwd client test`, `python -m devtools test-runner --type=e2e` y `python -m devtools app-check run` (§3) |
| devtools | `python -m devtools <comando> --help`, un caso real y uno de error |
| Hooks o configuración de agentes | `uv run pytest .claude/hooks/tests/test_hooks.py .agents/hooks` y la validación headless (`agent-config-testing.md`) |

## 2. Medir el audio

```bash
ffprobe -v error -show_entries format=duration -of csv=p=0 out/music/<AAAA-MM-DD>-<id>-<slug>/<archivo>.wav            # duración
ffmpeg -i out/music/<AAAA-MM-DD>-<id>-<slug>/<archivo>.wav -af ebur128 -f null - 2>&1 | tail -12                       # LUFS integrado y pico
ffmpeg -y -i out/music/<AAAA-MM-DD>-<id>-<slug>/<archivo>.wav -lavfi showspectrumpic=s=800x300 tmp/verificar/spec.png  # espectrograma
```

* La duración coincide con la pedida; el volumen está en el rango del README (sin clipping); el espectrograma no muestra cortes, silencios inesperados ni, en música, formantes de voz.
* El espectrograma lo abre el agente `image-reader` (Haiku), nunca la ventana principal: el hook `image_read_guard.py` lo bloquea.
* **El gusto lo decide el usuario**: entrégale las rutas clicables de `out/`. "Suena bien" no se afirma sin que lo escuche.

## 3. Verificar la app real: `app-check`, nunca Computer Use

* `python -m devtools app-check run [--scenario=<nombre>]... [--data=temp|real]` compila el binario de este worktree y lo abre aislado. Lo maneja con Playwright por CDP contra el server real, sin tocar el mouse ni el teclado del usuario: la ventana se ve, pero nadie la mueve. Exit 0 si todo pasa, 1 si falla un escenario, 2 si fallan la compilación o el arranque.
* Deja `tmp/app-check/<run>/report.json`, `shots/<sección>-<tema>.png` y `logs/app-check-<run>.log`. Las capturas las abre `image-reader`.
* `--data=temp` (por defecto) arranca de cero. `--data=real` muestra los motores, voces y salidas del usuario sobre una copia de su base con la cola en pausa, y aborta toda escritura a la API: sirve solo para mirar.
* `smoke` (por defecto) recorre cada sección en claro y en oscuro. Para un flujo, un escenario en `tests/e2e/app-check/<NN>-<flujo>.check.ts` con `test` de `fixture.ts`. Los diálogos nativos se simulan con `pickPaths` (archivo o carpeta) y `answerDialogs` (`confirm`) de `support/tauri.ts`.
* **Computer Use está prohibido en este repo**, en Claude Code, Codex y Antigravity: abre binarios viejos, espera aprobaciones que vencen y le quita el escritorio al usuario. Lo bloquea `.agents/hooks/computer_use_guard.py`. Si `app-check` no alcanza, se agrega un escenario o se deja una ficha en `docs/process/PENDING/`.

## 4. Transparencia

Si algo no se pudo correr (falta un venv, la GPU está ocupada por otra sesión, no hay credenciales), dilo explícitamente: *"Pasaron ruff y pytest; la corrida real con Qwen queda pendiente porque falta `server/data/narration/.venv-qwen`."* Nunca asumas que funciona porque no hay errores de sintaxis.

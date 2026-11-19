---
trigger: always_on
description: Un modelo a la vez en la GPU de 8 GB, también entre sesiones y worktrees; protocolo con gpu-turn, ListAgents y SendMessage
---

# Turno de la GPU entre sesiones — SIEMPRE ACTIVA

> En 8 GB no caben dos modelos: narración y música juntas, o dos sesiones narrando a la vez, desbordan la VRAM a la RAM compartida de WSL y todo va ~4× más lento. Adaptado del turno del stack de klinikae.

## Qué pide turno

Todo lo que carga un modelo: `narration tts`, `narration voices --build`, la evaluación con whisper (`server/data/narration/evaluation/`), `music` y `uv run pytest -m local` si importa torch en la GPU. No piden turno: ruff, `uv run pytest` (sin GPU), `--help` y ffmpeg.

## Protocolo

* **Siempre con el candado**: `python -m devtools gpu-turn run --job=<trabajo> -- <comando>` (desde cualquier worktree: el candado vive en `tmp/gpu-turn/` del checkout principal). Toma el turno al empezar y lo suelta al terminar, también con Ctrl+C o un error. Exit 1 si está ocupada. Los trabajos de `studio` no van así: ver la viñeta siguiente.
* **Trabajos de `studio` y del worker de la cola**: toman el candado de `server/src/content_studio/gpu_lock.py`, el mismo que usa `gpu-turn`. Un trabajo de GPU espera si otra sesión tiene la GPU, sin bloquear los de CPU. Cancelar un trabajo (`studio jobs cancel <id>`) termina su proceso. No los envuelvas en `gpu-turn run`: tomarían el candado dos veces.
* **Antes**: `gpu-turn status` (exit 0 libre, 1 ocupada; dice quién la tiene, la VRAM en uso y las sesiones abiertas del proyecto) y `ListAgents` para el nombre exacto de cada sesión.
* **Libre y sin otras sesiones**: corre, sin mensajes. **Libre con otras sesiones**: `SendMessage` a cada una con «ocupo la gpu: <trabajo> — <qué corre>» y corre.
* **Ocupada por otra sesión**: `SendMessage` a esa sesión pidiéndole que avise con «gpu libre»; `CronCreate` cada 10 min con «`gpu-turn status`; si está libre, toma el turno y sigue con la corrida» (solo mientras esperas). Mientras tanto sigue con lo que no usa GPU; si no queda nada, `Phase: external-wait`.
* **Al terminar** (éxito, fallo o interrupción): «gpu libre» por `SendMessage` a cada sesión abierta y `CronDelete` del respaldo. Si llegan dos «ocupo» a la vez, gana el primero recibido.
* Si recibes «gpu libre» u «ocupo la gpu», no respondas solo para acusar recibo: actúa según el estado.
* VRAM ocupada sin candado (otra app, un proceso colgado): `nvidia-smi`; no mates procesos ajenos sin preguntar.
* Corridas largas (HeartMuLa ~5 min por pista) en segundo plano, con la salida en `logs/` (`command-output.md`).

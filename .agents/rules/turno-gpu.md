---
trigger: always_on
description: Un modelo a la vez en la GPU de 8 GB, también entre sesiones y worktrees; protocolo con gpu-turn; mensajes solo a quien espera
---

# Turno de la GPU entre sesiones — SIEMPRE ACTIVA

> En 8 GB no caben dos modelos: narración y música juntas, o dos sesiones narrando a la vez, desbordan la VRAM a la RAM compartida de WSL y todo va ~4× más lento. Adaptado del turno del stack de klinikae.

## Qué pide turno

Todo lo que carga un modelo: `narration tts`, `narration voices --build`, la evaluación con whisper (`server/data/narration/evaluation/`), `music` y `uv run pytest -m local` si importa torch en la GPU. No piden turno: ruff, `uv run pytest` (sin GPU), `--help`, el asistente y ffmpeg.

## Protocolo

* **Siempre con el candado**: `python -m devtools gpu-turn run --job=<trabajo> -- <comando>` (desde cualquier worktree: el candado vive en `tmp/gpu-turn/` del checkout principal). Toma el turno al empezar y lo suelta al terminar, también con Ctrl+C o un error. Exit 1 si está ocupada.
* **El candado coordina; los mensajes no**. Antes de correr, solo `gpu-turn status` (exit 0 libre, 1 ocupada; dice quién la tiene y la VRAM en uso). Que haya otras sesiones abiertas no importa: si no tienen el candado, no usan la GPU.
* **Libre**: corre con `gpu-turn run`, sin mensajes a nadie (ni «ocupo la gpu» ni «gpu libre» al terminar).
* **Ocupada por otra sesión**: `ListAgents` para su nombre y un solo `SendMessage` a esa sesión pidiéndole que te avise con «gpu libre»; `CronCreate` cada 10 min con «`gpu-turn status`; si está libre, toma el turno y sigue con la corrida» (solo mientras esperas). Mientras tanto sigue con lo que no usa GPU; si no queda nada, espera el aviso.
* **Al terminar** (éxito, fallo o interrupción): «gpu libre» solo a las sesiones que te pidieron aviso, y `CronDelete` de tu respaldo si esperabas. Si dos piden el turno a la vez, gana la primera que lo toma con `gpu-turn run`.
* Si recibes «gpu libre», no respondas solo para acusar recibo: corre lo que esperabas.
* VRAM ocupada sin candado (otra app, un proceso colgado): `nvidia-smi`; no mates procesos ajenos sin preguntar.
* Corridas largas (HeartMuLa ~5 min por pista) en segundo plano, con la salida en `logs/` (`command-output.md`).

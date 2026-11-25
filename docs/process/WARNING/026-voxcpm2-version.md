# 026: voxcpm2 queda en Python 3.14 (pyahocorasick no tiene rueda cp315)

- **Contexto**: con torch 2.14.1+cu130 la resolución para 3.15 pasa, pero `pyahocorasick` 2.3.1 (dependencia de `textsearch`, a través de `voxcpm`) no tiene rueda `cp315` para Windows. `uv` la compila desde el código fuente y la instalación falla en el paso de pip (job 4, en `tmp/spec-026/home`).
- **Elegida**: Python 3.14 con torch 2.11.0+cu128 y torchaudio 2.11.0+cu128, voxcpm 2.0.3, huggingface-hub 1.33.0 y la revisión de HF `7936080b`. Instalación y salida corta verificadas: 2,06 s, 48 kHz mono, -16,0 LUFS, pico -3,0 dBFS.
- **Descartadas**: 3.15 con torch 2.14.1+cu130 (bloqueado por `pyahocorasick`); compilar `pyahocorasick` a mano (no es reproducible en la receta).
- **Cómo revertir**: poner `"version": "3.15"` y el par torch cu130 en `voxcpm2.json`, y reinstalar cuando haya rueda.
- **Cómo comprobarla**: en PyPI, `pyahocorasick` 2.3.1 no lista `cp315-cp315-win_amd64`; `uv run studio engines install voxcpm2` con la receta 3.14 (huella `df97cc`).
- **Pendiente**: [026-reintentar-voxcpm2](../PENDING/026-reintentar-voxcpm2.md).

# 026: acestep queda en Python 3.12 (su pyproject exige Python menor que 3.13 y torch 2.7.1)

- **Contexto**: ACE-Step 1.5 (commit `ca1e85fe`, HEAD de main) declara `requires-python >=3.11,<3.13` y fija `torch==2.7.1+cu128` para Windows. Con 3.13 o más no es instalable según su propio pyproject.
- **Elegida**: Python 3.12 con torch 2.7.1+cu128 (pin del upstream), torchaudio 2.7.1 y torchvision 0.22.1 (cu128), huggingface-hub 0.36.0 y soundfile 0.13.1, demucs 4.1.0 y las demás pins de su receta; revisiones de HF y commit de git sin cambio (ya son el `main`). Verificado: 30,0 s, -14,4 LUFS integrado, volumen medio -15,6 dB y pico -1,0 dBFS (sin recorte), voz no detectada por demucs (-42,4 dB).
- **Descartadas**: subir torch a 2.11 (el pyproject fija 2.7.1 y el código se probó con esa versión); 3.13 o más (lo impide `requires-python`).
- **Cómo revertir**: cuando ACE-Step permita Python 3.13 o más en su pyproject, subir la receta y repetir la medición.
- **Cómo comprobarla**: `uv run studio music --model acestep --style lofi-chill --duration 30 --evaluate` y comprobar `tracks.json` (`voice: false`).
- **Pendiente**: [026-reintentar-acestep](../PENDING/026-reintentar-acestep.md).

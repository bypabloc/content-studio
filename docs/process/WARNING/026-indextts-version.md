# 026: indextts queda en Python 3.11 sin verificar (licencia bilibili pendiente)

- **Contexto**: el pyproject upstream (commit `d9e41aa`) exige `requires-python >=3.10,<3.12` y `torch==2.8.*`, así que 3.11 es su techo. La licencia bilibili Model Use License no es comercial (AGENTS.md) y Motores exige aceptarla antes de instalar: la instalación falla al empezar (`engine_license_required`, job 14). Nunca llegó a instalar.
- **Elegida**: Python 3.11 con torch 2.8.0+cu128, torchaudio 2.8.0+cu128, torchvision 0.23.0+cu128 (pins upstream), huggingface-hub 0.35.0, soundfile 0.13.1 y la revisión de HF `c39ce5ba` (es el `main`). **Sin verificar**: no hay instalación ni salida corta.
- **Descartadas**: 3.12 (lo impide el `requires-python` upstream); torch 2.11 (rompería el pin `torch==2.8.*` sin probarlo); aceptar la licencia por el usuario.
- **Cómo revertir**: no aplica hasta que upstream permita 3.12 o cambie su pin de torch.
- **Cómo comprobarla**: que el usuario acepte la licencia en Motores; después `uv run studio engines install indextts` y `narration tts --model indextts`.
- **Pendiente**: [026-reintentar-indextts](../PENDING/026-reintentar-indextts.md).

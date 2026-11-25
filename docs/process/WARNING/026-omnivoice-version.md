# 026: omnivoice queda en Python 3.14 sin verificar (falta aceptar la licencia CC-BY-NC)

- **Contexto**: OmniVoice es CC-BY-NC + Higgs Audio 2 (no comercial). Motores exige que el usuario acepte la licencia (`license.accepted.omnivoice`) antes de instalar. Con la receta actual la instalación falla al empezar (`engine_license_required`, job 5). La resolución para 3.15 pasa (torch 2.14.1+cu130, torchaudio 2.11.1 de PyPI), pero no llegó a instalar.
- **Elegida**: Python 3.14 con torch 2.11.0+cu128 y torchaudio 2.11.0+cu128 (el par ya verificado en voxcpm2 y qwen) y la revisión de HF `c5fdb5cc` sin cambiar. **Sin verificar**: no hay instalación ni salida corta.
- **Descartadas**: aceptar la licencia por el usuario (la aceptación es suya); cambiar a la revisión nueva `3fc979d1` (2026-11-20) sin probarla; dejar 3.15 sin prueba.
- **Cómo revertir**: poner `"version": "3.15"`, el par torch cu130 y la revisión `3fc979d1` si la prueba lo permite.
- **Cómo comprobarla**: que el usuario acepte la licencia en Motores (o en la base de prueba, con su consentimiento) y después `uv run studio engines install omnivoice` y `narration tts --model omnivoice`.
- **Pendiente**: [026-reintentar-omnivoice](../PENDING/026-reintentar-omnivoice.md).

# 004: la narración recomienda VoxCPM2, no Qwen 0.6B como sugería el plan

- **Contexto**: el plan de la 004 sugería Qwen3-TTS 0.6B como recomendado de narración. El README de narración marca VoxCPM2 como recomendado. Cada selector del catálogo necesita una sola estrella.
- **Elegida**: VoxCPM2 para narración, porque es la fuente que el usuario lee; ACE-Step para música (el README de música lo marca). Ambas marcas van en `recommended` de `narration/engines/registry.py` y `music/engines/registry.py`.
- **Descartadas**: Qwen 0.6B (el README no lo marca); dos recomendados por selector (el selector no tendría un default claro).
- **Cómo revertir**: cambiar `recommended` en los dos `registry.py`.
- **Cómo comprobarla**: `uv run pytest server/tests/unit/src/content_studio/narration/engines/test_registry.py` y una narración real con VoxCPM2 en la T9, con `gpu-turn run`.
- **Antes de `main`**: esa narración real (T9) y la licencia de VoxCPM2 para uso comercial, según la tabla de `AGENTS.md`.

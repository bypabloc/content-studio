# 026: las salidas para escuchar se perdieron

- **Qué**: las salidas de `out/narration` y `out/music` (los WAV que lista el PR #109) estaban en el worktree `026-engines-python`. Al cerrarlo, la carpeta quedó sin `out/` ni `server/` (solo `docs/`, `tmp/` y `uv.lock`).
- **Qué queda**: `tmp/spec-026/` (espectrogramas y checks) y las medidas de `docs/process/01-done/narration.md` y `music.md`.
- **Causa**: no investigada. Revisar que el cierre de worktrees no borre carpetas en uso.
- **Quién decide**: usuario.
- **Qué lo cierra**: regenerar las salidas con `uv run studio narration tts` y `music` (con `gpu-turn`), o recuperar una copia si existe.

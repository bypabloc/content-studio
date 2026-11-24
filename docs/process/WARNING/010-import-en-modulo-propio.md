# 010: la ruta de importar vive en `api/routes/voices_import.py`

- **Contexto**: el test `test_voices_import.py` (AC-6) no tenía módulo espejo. La auditoría del espejo (`test-runner`, etapa `unit`) lo marcó como huérfano mientras la ruta estaba en `voices.py`.
- **Elegida**: un módulo propio, `api/routes/voices_import.py`, con `POST /voices/profiles/{slug}/import`, espejo de su test. Reusa `_profile` y `_style` de `voices.py`.
- **Descartadas**: renombrar el test a `test_voices.py` (ese archivo ya cubre las demás rutas de voces y la spec nombra `test_voices_import.py`); dejar la ruta en `voices.py` con el test huérfano (la auditoría lo rechaza).
- **Cómo revertir**: pasar la ruta a `voices.py` y renombrar el test a `test_voices.py` (un solo commit).
- **Cómo comprobarla**: `python -m devtools test-runner --type=unit` (incluye `test_ac3_real_repo_mirror_passes`) y `uv run pytest server/tests/unit/src/content_studio/api`.
- **Pendiente**: ninguno.

# 010: el gate i18n cuenta las claves que el server usa con `t('…')`

- **Contexto**: el server llama `messages.t('clave')` desde Python (los `voice.check.*` y `voice.consent.import`). El detector solo leía el client, así que esas claves salían como sin uso. Para que no se borraran, `voice.check.` estaba declarado como prefijo dinámico en `tests/validators/i18n.json`.
- **Elegida**: el detector recorre con `ast` los `.py` de `server/src/content_studio` y cuenta cada `t('…')` con texto literal como uso, igual que las claves del client. Se quita `voice.check.` de `dynamicPrefixes`, porque sus claves ya aparecen literales en `services/voice_check.py`. Los prefijos quedan solo para claves armadas en runtime.
- **Descartadas**: dejar el prefijo dinámico (esconde claves sin uso y tapa errores de escritura); buscar `t(` con una regex (falla con llamadas repartidas en varias líneas).
- **Cómo revertir**: volver a poner `voice.check.` en `dynamicPrefixes` y quitar `server_keys` de `devtools/test_runner/i18n.py` (commit `fix:` aparte).
- **Cómo comprobarla**: `uv run pytest devtools/tests/unit/test_runner/test_i18n.py` (incluye los dos tests de `t()` en Python y el repo real) y la etapa `i18n` del gate.
- **Pendiente**: ninguno.

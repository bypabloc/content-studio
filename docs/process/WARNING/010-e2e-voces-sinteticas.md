# 010: las respuestas e2e de Mis voces son sintéticas, y el harness deja pasar cuerpos binarios

- **Contexto**: la spec pide las respuestas «grabadas» en `_api/voices/`. Una captura de un server real tendría las voces del usuario (`reference/`), y no se versionan. Además, `mockApi` hacía `JSON.parse` de todo cuerpo de POST, y la toma subida es un WAV.
- **Elegida**: las respuestas de `_api/voices/` se escriben a mano según el contrato de la API y usan datos ficticios («Ana», «yesid», «maria»). `mockApi` pasa a `null` un cuerpo que no es JSON; la prueba de la toma mira solo el camino. Los cinco e2e corren con el micrófono simulado de Chromium (`launchOptions` en `playwright.config.ts`).
- **Descartadas**: capturar del server real (expone voces del usuario) y omitir la prueba de la subida (es el criterio AC-8).
- **Cómo revertir**: borrar `tests/e2e/_api/voices/` y `tests/e2e/support/voices.ts`, y los cinco archivos `*.e2e.ts` de `voices/` y `recording/`.
- **Cómo comprobarla**: `python -m devtools test-runner --type=e2e` (no está en `all`: corre a mano en cada spec que toca la UI).

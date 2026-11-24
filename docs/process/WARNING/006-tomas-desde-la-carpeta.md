# 006: el resultado lee la toma de su carpeta; no hay endpoint nuevo

- **Contexto**: el resultado necesita el .wav, los párrafos, la evaluación y el volumen de una toma. `Job.result` existe en el esquema, pero el worker nunca lo escribe.
- **Elegida**: `NarrationResult` lee `script.json` (el nombre del .wav y los párrafos) y `<wav>.json` (la evaluación de whisper) con `GET /files`, y la onda y el LUFS con `/media/*`. Las observaciones del motor llegan en inglés y el cliente las traduce al mostrarlas (diferencias, silencios y ritmos); las que no reconoce salen tal cual, aparte.
- **Descartadas**: rellenar `Job.result` desde el worker (cambia el ciclo de la cola, y la spec no lo pide); un endpoint `/takes` (una ruta más sin AC que la pida).
- **Cómo revertir**: no aplica (solo lee). Si cambia la forma de `script.json` o del `.json` de la toma, cambian los tipos `Script` y `Take` de `NarrationResult.tsx`.
- **Cómo comprobarla**: `client/tests/unit/src/features/narration/NarrationResult.test.tsx`.
- **Antes de**: el merge a `dev`.

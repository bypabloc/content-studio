# 006: regenerar reconstruye los bloques desde `script.json`; no guarda el estado del motor

- **Contexto**: el `pb` de cada bloque puede traer `emo` con arrays de numpy (IndexTTS, `vector`) u objetos del motor. No se puede serializar a JSON sin perder datos ni inventar un formato.
- **Elegida**: `script.json` guarda los insumos: segmentos, referencia, estilo, idioma, master, LUFS, semillas por bloque y por ronda, y el nombre del `.wav`. Rehacer un bloque llama a `prepare_blocks` con esos datos, igual que la narración original, así que la traducción, la emoción y la referencia salen iguales. Los bloques que no cambian se copian byte a byte (`shutil.copyfile`), para que su hash no cambie (AC-3). La toma nueva sale en `out/narration/` (el worker usa la familia del tipo, no `narration.regenerate`), y el CLI pide el párrafo desde 0, como el test.
- **Descartadas**: serializar `pb` completo (`emo` no es JSON); mantener el motor cargado entre trabajos (bloquea la GPU para la música, D-2); recodificar los bloques desde memoria (el hash cambiaría si cambia el escritor, aunque el audio sea el mismo).
- **Cómo revertir**: quitar `narration/takes.py`, el servicio `narration.regenerate` y sus flags internos; las tomas nuevas dejan de poder hacerse.
- **Cómo comprobarla**: `uv run pytest server/tests/unit/src/content_studio/narration/test_takes.py` (AC-3: bloques 0 y 2 con el mismo hash, el 1 distinto, la original sin cambios).
- **Pendiente**: la corrida real con `voxcpm2` en la verificación final (T9).

# 010: la entrada del catálogo de voces pone la consola en errors=replace (cp1252)

- **Contexto**: el build imprime un resultado por estilo con «←» (las razones de un estilo rechazado con comprobaciones). En Windows, la consola y la tubería de la cola usan cp1252, que no tiene esa flecha: `print` reventaba con `UnicodeEncodeError` después de generar el estilo y antes de guardar `aprobacion.json`. Lo encontró la verificación en copia del build (`logs/verificar-build-copia-010-t9.log`); los tests no lo veían porque corren con stdout en UTF-8.
- **Elegida**: `process.console_utf8()` al inicio de `narration/voices/main.py::main()`, el mismo arreglo que ya usan `studio` (`cli/main.py`) y la música (`music_main.py`). El proceso del venv de CosyVoice vuelve a entrar en `main()`, así que cubre el CLI y la cola de trabajos.
- **Descartadas**: cambiar «←» por ASCII (arregla esta línea, pero el próximo símbolo fuera de cp1252 volvería a reventar). Forzar UTF-8 en el entorno de la cola (cambia el proceso de fuera, no la entrada del módulo).
- **Cómo revertir**: quitar la línea `process.console_utf8()` de `main()`. Un estilo rechazado volvería a reventar en Windows.
- **Cómo comprobarla**: `server/tests/unit/src/content_studio/narration/voices/test_main.py` (regresión) y la corrida en copia: `RESULT nick …` en `logs/verificar-build-copia-010-t9b.log`.

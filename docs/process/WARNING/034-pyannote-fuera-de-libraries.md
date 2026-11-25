# 034: pyannote fuera de LIBRARIES hasta que tenga su EngineSpec

- **Contexto**: `test_imports_the_engine` busca cada entrada de `LIBRARIES` en los registros de narración y música (`_specs()`). La familia `diarization` no tiene todavía un registro propio, así que `LIBRARIES['pyannote']` daba `KeyError`. La F1 la había agregado por el archivo de fase.
- **Elegida**: quitar la entrada en la verificación final. La familia `diarization` (la 035) aporta su `EngineSpec` y la entrada vuelve a `LIBRARIES` junto con ella.
- **Descartadas**: extender `_specs()` con un registro de pyannote aquí, porque la 034 no crea el motor (la 035 sí).
- **Cómo revertir**: volver a agregar `'pyannote': 'pyannote.audio'` a `LIBRARIES` cuando exista el registro de diarización.
- **Cómo comprobarla**: `uv run pytest -m local server/tests/integration/test_venvs.py -q` sin errores de `KeyError`.
- **Pendiente**: ninguno.

# 006: la toma regenerada no se evalúa con whisper; Comparar la muestra como «Sin evaluar»

- **Contexto**: `narration.regenerate` rehace un párrafo de una toma que sí se evaluó. Su comando pasa solo `--model`, `--from-script`, `--only`, `--output` y `--seed` (`services/narration_regenerate.py`, `build_command`). No pasa `--evaluate`, así que la toma nueva no tiene `evaluation` y su tarjeta en Comparar dice «Sin evaluar».
- **Elegida**: dejar «Sin evaluar». Es lo que se sabe de la toma nueva: no se ha transcrito con whisper.
- **Por qué no se evalúa**: `evaluate()` (`narration/pipeline.py`) transcribe la toma entera y reintenta los bloques con error (`--retries`). Esos reintentos regeneran bloques ajenos al párrafo y cambian su hash, lo que rompe AC-3 (los bloques 0 y 2 deben quedar idénticos a la original).
- **Descartadas**: pasar `--evaluate` a la regeneración (rompe AC-3 con reintentos); copiar la evaluación de la original (describiría un audio que la toma nueva no tiene).
- **Cómo revertir**: no aplica; no hay código nuevo en esta decisión.
- **Cómo comprobarla**: `server/tests/unit/src/content_studio/services/test_narration_regenerate.py` (AC-3) y la corrida real: `tmp/spec-006/drive.mjs` comprueba «Sin evaluar» en la tarjeta de la toma regenerada.
- **Qué la cierra**: [PENDING 006-evaluar-toma-regenerada](../PENDING/006-evaluar-toma-regenerada.md).
- **Antes de**: el pase a `main`. No bloquea el merge a `dev`.

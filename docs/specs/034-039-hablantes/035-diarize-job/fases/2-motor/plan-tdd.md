# Spec 035, fase 2: motor en su venv y audio por hablante

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación.
> Cada una queda anotada en [`docs/process/WARNING/`](../../../../../process/WARNING/README.md) (ficha `035-<tema>.md` con contexto, elegida, descartadas, cómo revertir y cómo comprobarla, y su fila en el README de la carpeta).
> Toda revisión pendiente queda en [`docs/process/PENDING/`](../../../../../process/PENDING/README.md) (ficha y fila, con qué la cierra).
>
> **Datos del usuario: solo los que crea esta spec**. La spec no borra ni sobrescribe voces grabadas (`server/data/narration/voz/`), voces construidas, salidas de `out/` ni modelos descargados que ella no creó. Sus pruebas escriben en carpetas nuevas (`out/<herramienta>/spec-035/` o `tmp/spec-035/`). Si algo parece exigir tocar datos existentes, no se decide al ejecutar: es un `blocked — user-data` y se pregunta. Los cambios locales o sin rastrear del checkout principal no son de la spec: no se tocan y no bloquean.

**Objetivo**: `diarize_main` corre pyannote como dice D-2, y `speaker_audio` arma el ffmpeg de un hablante. **AC**: AC-4, AC-5, AC-6. **Depende de**: F1.

## Ciclos TDD

#### Ciclo C3: `diarize_main` [AC-4]

- **RED**: `server/tests/unit/src/content_studio/diarization/test_diarize_main.py::test_ac4_entorno_y_salida`
  - Se simulan `use_venv`, `pyannote.audio.Pipeline` y `torch` con un módulo falso en `sys.modules`, y se usa un WAV de 2 s generado con `wave`.
  - THEN se cumple todo lo de AC-4: entorno, ruta local, lote 4, dict de entrada, progreso creciente y archivos.
  - Con `--speakers 2` pasa `num_speakers=2`; con un rango pasa `min_speakers` y `max_speakers`.
- **GREEN**: `diarization/diarize_main.py`. Verify: `uv run pytest server/tests/unit/src/content_studio/diarization/test_diarize_main.py -q`.
- **REFACTOR**: ninguno.

#### Ciclo C4: audio por hablante [AC-5]

- **RED**: `test_speaker_audio.py::test_ac5_comando_ffmpeg`
  - Given 3 turnos de `SPEAKER_01` When `split_command` Then el filtro silencia fuera de esos tramos y conserva el códec PCM. Con 2000 turnos, el filtro va en un archivo.
  - Además, un test `local` (`@pytest.mark.local`) con ffmpeg real sobre un tono de 5 s: misma duración ±10 ms.
- **GREEN**: `diarization/speaker_audio.py`. Verify: `uv run pytest server/tests/unit/src/content_studio/diarization/test_speaker_audio.py -q`.
- **REFACTOR**: ninguno.

#### Ciclo C5: verificación del motor [AC-6]

- **RED**: `server/tests/unit/src/content_studio/engines/test_verification.py::test_ac6_familia_diarization`
  - Con `subprocess` simulado: genera el audio de prueba de 6 s, llama a `diarize_main` y acepta un `turns.json` válido. Un JSON inválido da un fallo con su motivo.
- **GREEN**: `engines/verification.py`, rama `diarization`. Verify: `uv run pytest server/tests/unit/src/content_studio/engines -q`.
- **REFACTOR**: ninguno.

## Matriz e2e

No aplica.

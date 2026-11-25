# Spec 030, fase 1: Tablas, sondeo y recibos

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación.
> Cada una queda anotada en [`docs/process/WARNING/`](../../../../../process/WARNING/README.md) (ficha `030-<tema>.md` con contexto, elegida, descartadas, cómo revertir y cómo comprobarla, y su fila en el README de la carpeta).
> Toda revisión pendiente queda en [`docs/process/PENDING/`](../../../../../process/PENDING/README.md) (ficha y fila, con qué la cierra).
>
> **Datos del usuario: solo los que crea esta spec**. La spec no borra ni sobrescribe voces grabadas (`server/data/narration/voz/`), voces construidas, salidas de `out/` ni modelos descargados que ella no creó. Sus pruebas escriben en carpetas nuevas (`out/<herramienta>/spec-030/` o `tmp/spec-030/`). Si algo parece exigir tocar datos existentes, no se decide al ejecutar: es un `blocked — user-data` y se pregunta. Los cambios locales o sin rastrear del checkout principal no son de la spec: no se tocan y no bloquean.

**Objetivo**: Una carpeta registrada procesa lo que se suelta y deja el resultado al lado. **AC**: AC-1, AC-2, AC-3, AC-4, AC-5, AC-6, AC-7, AC-8. **Depende de**: nada.

## Ciclos TDD

Ordenados por dependencia (utilidades → parser y registro → motor, servicio o comando → CLI y API → client). La numeración de ciclos es global a la spec; todo AC queda cubierto por al menos un ciclo y un fix empieza con un test de regresión en `server/tests/integration/test_bugs.py`.

#### Ciclo C1: Registrar carpetas [AC-1]

- **RED**: `server/tests/unit/src/content_studio/inbox/test_store.py::test_ac1_registers_a_valid_folder_and_rejects_the_rest`
  - WHEN se registra una carpeta inexistente THEN `folder_not_found`; con `params` inválidos, los errores del servicio.
  - Falla por el motivo esperado, no por setup.
- **GREEN**: migración, `inbox/store.py`, `inbox/inputs.py`. Verify: `uv run pytest server/tests/unit/src/content_studio/inbox -q`.
- **REFACTOR**: ninguno.

#### Ciclo C2: Archivo estable [AC-2, AC-3]

- **RED**: `server/tests/unit/src/content_studio/inbox/test_scanner.py::test_ac2_takes_a_file_once_it_is_stable_across_two_sweeps`
  - Given un archivo en `tmp_path` When `scan_once` corre dos veces sin cambios Then se mueve a `processing/` y hay un trabajo; si crece entre sondeos, no.
  - Falla por el motivo esperado, no por setup.
- **GREEN**: `inbox/scanner.py`. Verify: `uv run pytest server/tests/unit/src/content_studio/inbox -q`.
- **REFACTOR**: ninguno.

#### Ciclo C3: Recibos [AC-4, AC-5]

- **RED**: `server/tests/unit/src/content_studio/inbox/test_receipts.py::test_ac4_done_keeps_the_original_outputs_and_a_result_receipt`
  - Given un trabajo terminado con un `.mp3` en `output_dir` When llega su evento Then `done/<nombre>/` tiene original, salida y recibo.
  - Falla por el motivo esperado, no por setup.
- **GREEN**: `inbox/receipts.py` suscrito al `Broker`. Verify: `uv run pytest server/tests/unit/src/content_studio/inbox -q`.
- **REFACTOR**: ninguno.

#### Ciclo C4: `.job.json` [AC-6]

- **RED**: `server/tests/unit/src/content_studio/inbox/test_scanner.py::test_ac6_job_file_with_relative_paths_is_queued_or_failed`
  - WHEN se suelta un `.job.json` con `"input": "a.wav"` THEN el trabajo recibe la ruta absoluta dentro de la carpeta; uno inválido va a `failed/`.
  - Falla por el motivo esperado, no por setup.
- **GREEN**: lectura del JSON en `scanner.py`. Verify: `uv run pytest server/tests/unit/src/content_studio/inbox -q`.
- **REFACTOR**: ninguno.

#### Ciclo C5: Reinicios y `keep_awake` [AC-7, AC-8]

- **RED**: `server/tests/integration/test_inbox.py::test_ac7_does_not_reprocess_after_a_restart`
  - Given `inbox_items` con un archivo `done` When el server arranca Then no lo encola; un archivo nuevo sí. Con `keep_awake`, `IdleClock.idle()` es False.
  - Falla por el motivo esperado, no por setup.
- **GREEN**: barrido inicial y `hold`/`release` del `IdleClock`. Verify: `uv run pytest server/tests/integration/test_inbox.py -q`.
- **REFACTOR**: ninguno.

## Matriz e2e

No aplica: esta fase no crea ni cambia un flujo del client.

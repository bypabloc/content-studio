# Spec 034, fase 1: receta, familia y token en la instalación

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación.
> Cada una queda anotada en [`docs/process/WARNING/`](../../../../../process/WARNING/README.md) (ficha `034-<tema>.md` con contexto, elegida, descartadas, cómo revertir y cómo comprobarla, y su fila en el README de la carpeta).
> Toda revisión pendiente queda en [`docs/process/PENDING/`](../../../../../process/PENDING/README.md) (ficha y fila, con qué la cierra).
>
> **Datos del usuario: solo los que crea esta spec**. La spec no borra ni sobrescribe voces grabadas (`server/data/narration/voz/`), voces construidas, salidas de `out/` ni modelos descargados que ella no creó. Sus pruebas escriben en carpetas nuevas (`out/<herramienta>/spec-034/` o `tmp/spec-034/`). Si algo parece exigir tocar datos existentes, no se decide al ejecutar: es un `blocked — user-data` y se pregunta. Los cambios locales o sin rastrear del checkout principal no son de la spec: no se tocan y no bloquean.

**Objetivo**: la receta `pyannote` valida, y el paso `hf` restringido recibe el token sin exponerlo y falla con un código propio. **AC**: AC-1, AC-2, AC-3. **Depende de**: nada.

## Ciclos TDD

#### Ciclo C1: receta y familia [AC-1]

- **RED**: `server/tests/unit/src/content_studio/engines/test_recipes.py::test_ac1_pyannote_recipe`
  - WHEN `recipes.load('pyannote')` THEN se cumple todo lo de AC-1. Un `gated` que no es booleano da `ValueError`.
- **GREEN**: `recipes.py` (`FAMILIES`, `OPTIONAL['hf']` y `Recipe.gated`) y `recipes/pyannote.json`. Verify: `uv run pytest server/tests/unit/src/content_studio/engines/test_recipes.py -q`.
- **REFACTOR**: ninguno.

#### Ciclo C2: token en el entorno [AC-2]

- **RED**: `server/tests/unit/src/content_studio/engines/test_steps.py::test_ac2_token_en_env_no_en_argv`
  - Given un paso `hf` restringido y `subprocess.run` simulado When se ejecuta con `token='hf_x…'` Then `env['HF_TOKEN']` es el token y no aparece en `args`. En un paso sin `gated`, `HF_TOKEN` no está en el `env` aunque exista en `os.environ`.
  - `test_installer.py::test_ac2_token_stays_out_of_install_json_and_log`: el token no aparece en `install.json` ni en el log.
- **GREEN**: `steps.execute_step` e `installer.install`. Verify: `uv run pytest server/tests/unit/src/content_studio/engines -q`.
- **REFACTOR**: ninguno.

#### Ciclo C3: repositorio restringido [AC-3]

- **RED**: `test_steps.py::test_ac3_gated_repo_exits_25`
  - Given `HfApi.model_info` simulado que lanza `GatedRepoError`, y otro con un `HfHubHTTPError` 403, When corre `_download` Then el proceso sale con 25 y stderr trae el mensaje sin el token.
- **GREEN**: `steps._download` e `installer.EXIT_CODES`. Verify: `uv run pytest server/tests/unit/src/content_studio/engines -q`.
- **REFACTOR**: ninguno.

## Matriz e2e

No aplica.

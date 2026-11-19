# 003: plan

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación. Cada una queda en [`docs/process/WARNING/`](../../../process/WARNING/README.md); toda revisión pendiente, en [`docs/process/PENDING/`](../../../process/PENDING/README.md).
>
> **Datos del usuario: solo los que crea esta spec**. No borra ni sobrescribe voces grabadas, voces construidas, salidas de `out/` ni modelos que no creó; si algo parece exigirlo, es un `blocked — user-data`.

## 1. Ciclos TDD

Antes del ciclo 1: `uv run pytest -q --co | tail -1` en `origin/dev`, anotado en el handoff (base de AC-9).

#### Ciclo 1: esqueleto del runner [AC-8]

- **RED**: `devtools/tests/unit/test_runner/test_main.py`. `--type=foo` sale con exit 2, y `--type=lint` sobre un repo limpio imprime una línea JSON `{"stage":"lint","status":"pass"}` con exit 0.
- **GREEN**: `main.py`, `flags.py`, `changeset.py` y `lint.py` (D-1).
- **REFACTOR**: ninguno.

#### Ciclo 2: validador de tamaño [AC-1, AC-2]

- **RED**: `test_validators.py`, con los casos de AC-1 y AC-2 en `tmp_path` y una configuración mínima.
- **GREEN**: `validators.py`, `tests/validators/file-size.json` y la generación inicial de `file-size.baseline.json` con `--write-baseline`. `test_structure.py` deja de medir líneas.
- **REFACTOR**: ninguno.

#### Ciclo 3: mover los tests al espejo [AC-9]

- **RED**: ninguno nuevo. Es un movimiento con `git mv`, y la red es AC-9: el mismo total de tests.
- **GREEN**: los tests unitarios a `server/tests/unit/src/content_studio/...` y los de integración a `server/tests/integration/` (D-3). Lo mismo en `devtools/tests/unit/`. Se ajustan `conftest.py`, `testpaths` y las rutas de las fixtures.
- **REFACTOR**: un test que mezcla dos módulos se parte en dos espejos.

#### Ciclo 4: auditoría del espejo [AC-3]

- **RED**: `test_unit.py::test_ac3_*`, con los tres motivos de falla sobre un árbol falso.
- **GREEN**: la auditoría en `unit.py`, `tests/validators/mirror.baseline.json` y los exentos por patrón.
- **REFACTOR**: ninguno.

#### Ciclo 5: cobertura por archivo [AC-4]

- **RED**: `test_unit.py::test_ac4_cobertura_por_archivo`, con un módulo de fixture al 70 % y otro al 80 %.
- **GREEN**: `pytest-cov` en el grupo `dev`, lectura de `coverage.json`, `coverage.baseline.json` y `omit` (D-4).
- **REFACTOR**: ninguno.

#### Ciclo 6: docstrings y typecheck [AC-5, AC-6]

- **RED**: `test_lint.py::test_ac5_docstring_obligatorio` y `test_typecheck.py::test_ac6_*`, cada uno con un archivo de fixture.
- **GREEN**: ruff `D1` (con `convention = "google"`) en `pyproject.toml`, más los docstrings que falten en `server/src` y `devtools` (en español). mypy en el grupo `dev`, su sección `[tool.mypy]` y los overrides que hagan falta (PENDING).
- **REFACTOR**: ninguno.

#### Ciclo 7: tdd y guard-tdd [AC-7]

- **RED**: `test_guard_tdd.py`, con y sin archivos en `tdd/`.
- **GREEN**: `tdd.py` y `guard_tdd.py`.
- **REFACTOR**: el chequeo que hoy tiene `pre-push` se borra y pasa a llamar al runner.

#### Ciclo 8: hooks, CI y reglas [AC-8]

- **RED**: `test-runner --type=all` en el repo real.
- **GREEN**: D-6. Se actualizan `.git-hooks/pre-commit`, `pre-push`, `calidad.yml`, las reglas (`testing.md`, `codigo-python.md`, `devtools.md`, `git-workflow.md`) y las skills (`testing`, `tdd-workflow`, `fix-hooks`, `devtools`). Después, `python -m devtools rules --sync`.
- **REFACTOR**: ninguno.

## 2. Archivos

| Acción | Archivo | Verify |
| :--- | :--- | :--- |
| Crear | `devtools/test_runner/{__init__,main,flags,changeset,lint,spelling,validators,typecheck,unit,tdd,guard_tdd}.py` | `uv run pytest devtools/tests -q` |
| Crear | `devtools/tests/unit/test_runner/test_*.py` | ídem |
| Crear | `tests/validators/file-size.json`, `file-size.baseline.json`, `mirror.baseline.json`, `coverage.baseline.json` | `test-runner --type=validators` |
| Mover | `server/tests/*.py` → `server/tests/unit/src/...` y `server/tests/integration/` | `uv run pytest -q --co` |
| Modificar | `pyproject.toml` (pytest-cov, mypy, ruff `D1`, testpaths), `uv.lock` | `uv sync` |
| Modificar | `.git-hooks/pre-commit`, `pre-push`, `.github/workflows/calidad.yml` | `test-runner --type=all` |
| Modificar | reglas y skills de D-6 | `agent-context`, `rules` |

## 3. Tareas

| Tarea | Archivos | AC | Depende de | Verify | Done |
| :--- | :--- | :--- | :--- | :--- | :--- |
| T1 | Esqueleto y lint | AC-8 | — | `uv run pytest devtools/tests -q` | [x] |
| T2 | Validador de tamaño | AC-1, AC-2 | T1 | ídem | [x] |
| T3 | Tests al espejo | AC-9 | — | `uv run pytest -q --co \| tail -1` | [x] |
| T4 | Auditoría del espejo | AC-3 | T1, T3 | ídem | [x] |
| T5 | Cobertura | AC-4 | T4 | ídem | [x] |
| T6 | Docstrings y typecheck | AC-5, AC-6 | T1 | `test-runner --type=lint,typecheck` | [x] |
| T7 | tdd y guard-tdd | AC-7 | T1 | ídem | [x] |
| T8 | Hooks, CI y reglas | AC-8 | T2–T7 | `test-runner --type=all` | [x] |

## 4. Commits

1. `chore: devtools test-runner con etapa lint` (T1).
2. `chore: validador de tamaño por categoría con baseline` (T2).
3. `test: tests del server y de devtools en rutas espejo` (T3).
4. `chore: auditoría de tests espejo y huérfanos` (T4).
5. `chore: cobertura mínima del 80 % por archivo` (T5).
6. `chore: docstrings obligatorios y typecheck con mypy` (T6).
7. `chore: etapas tdd y guard-tdd` (T7).
8. `ci: pre-commit, pre-push y calidad usan el test-runner` (T8 y las fichas).

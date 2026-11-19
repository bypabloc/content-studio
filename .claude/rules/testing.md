---
paths:
  - "server/tests/**"
  - "server/src/**"
---

# Testing: tipos, ubicación y ciclo TDD

Runner único de gates: `python -m devtools test-runner --type=all` (lint, spelling, validators, unit, typecheck y tdd; spec 003), lo mismo que la CI en 3.10 y 3.12. Por debajo corre `uv run pytest` (con `--doctest-modules`; sin GPU). `uv run pytest -m local` suma los que necesitan los venvs de los motores de este equipo. Ciclo y comandos: skill `tdd-workflow`.

Un fallo que solo da la CI (Linux) no se reproduce en WSL (`command-output.md`).

## 1. Tipos

| Tipo | Dónde | Qué prueba | Corre en CI |
| :--- | :--- | :--- | :--- |
| Doctest | El docstring de la función en `server/src/` | Funciones puras chicas: parsers, rutas, formatos | Sí |
| Caracterización | `server/tests/integration/test_characterization.py` + `server/tests/integration/fixtures/` | Que la salida de los parsers y bloques no cambie sin querer | Sí |
| Tamaño, espejo, cobertura, docstrings y tipos | `test-runner` (`devtools/tests/unit/test_runner/`) | Límites de `file-size.json`, espejo sin huérfanos, 80 % por archivo, D1 y mypy | Sí |
| Estructura | `tests/validators/test_structure.py` | Reglas de `codigo-python.md`: sintaxis 3.10, código solo en `server/src/`, `.agents`/`.claude` en sincronía | Sí |
| Bugs | `server/tests/integration/test_bugs.py` | Un test de regresión por bug, que lo reproduce | Sí |
| CLI y asistente | `server/tests/integration/test_cli.py`, `server/tests/unit/src/content_studio/cli/test_flow.py` | Typer, flags y el asistente sin TTY | Sí |
| Registro | `server/tests/unit/src/content_studio/narration/engines/test_registry.py` | Motores y comandos registrados | Sí |
| Hooks y devtools | `.claude/hooks/tests/test_hooks.py`, `.agents/hooks/tests/`, `devtools/tests/unit/` | Hooks de agentes y devtools, ejecutados de verdad | Sí |
| Local | `server/tests/integration/test_venvs.py` (`@pytest.mark.local`) | Cada venv importa su librería | No (`-m local`) |
| tdd efímero | `server/tests/tdd/test_<pieza>.py` o `devtools/tests/tdd/` | Razonar una pieza antes de su test permanente | **Nunca**: `guard-tdd` (pre-push y CI) falla si existe |

* Un test unitario va en su ruta espejo: `server/tests/unit/src/content_studio/<ruta>/test_<módulo>.py` o `devtools/tests/unit/<ruta>/test_<módulo>.py`. Lo que cruza módulos va a `server/tests/integration/`. La etapa `unit` falla si falta el espejo de un módulo (salvo lo que lista `tests/validators/mirror.baseline.json`) y exige 80 % de cobertura por archivo del changeset.
* Si un cambio de comportamiento es a propósito, las fixtures se regeneran con `uv run python server/tests/integration/fixtures/generate.py` en un commit aparte.

## 2. Qué mockear

* Nunca la función bajo prueba. Sí: el reloj, la GPU y los motores (los tests de CI no cargan modelos), `subprocess` hacia ffmpeg cuando solo importa el comando armado.
* Lo que depende de un modelo real se verifica con la corrida real y sus mediciones (`verify-before-claiming-done.md`), no con un mock: un mock no dice si el audio suena bien.
* Tests sin red ni descargas: lo que baje un modelo es `local` o no es un test.

## 3. TDD

1. **RED**: el test (o el doctest) primero, con el AC en el nombre (`test_ac2_corta_en_silencio`) o en el docstring; ver que falla por el motivo esperado, no por el setup.
2. **GREEN**: lo mínimo para el verde, con `uv run pytest <archivo>::<test>`.
3. **REFACTOR** con la red en verde; cerrar con `uv run ruff check && uv run ruff format --check && uv run pytest`.
* Un fix de bug empieza con su test de regresión en `server/tests/integration/test_bugs.py`, rojo con el código actual.
* Un test flaky es un fallo. Nada de `sleep` ni timeouts fijos: espera la señal real.

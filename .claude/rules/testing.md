---
paths:
  - "tests/**"
  - "src/**"
---

# Testing: tipos, ubicación y ciclo TDD

Runner único: `uv run pytest` (con `--doctest-modules`; sin GPU, lo mismo que la CI en 3.10 y 3.12). `uv run pytest -m local` suma los que necesitan los venvs de los motores de este equipo. Ciclo y comandos: skill `tdd-workflow`.

## 1. Tipos

| Tipo | Dónde | Qué prueba | Corre en CI |
| :--- | :--- | :--- | :--- |
| Doctest | El docstring de la función en `src/` | Funciones puras chicas: parsers, rutas, formatos | Sí |
| Caracterización | `tests/test_caracterizacion.py` + `tests/fixtures/` | Que la salida de los parsers y bloques no cambie sin querer | Sí |
| Estructura | `tests/test_estructura.py` | Reglas de `codigo-python.md`: 300 líneas, sintaxis 3.10, código solo en `src/`, `.agents`/`.claude` en sincronía | Sí |
| Bugs | `tests/test_bugs.py` | Un test de regresión por bug, que lo reproduce | Sí |
| CLI y asistente | `tests/test_cli.py`, `tests/test_asistente.py` | Typer, flags y el asistente sin TTY | Sí |
| Registro | `tests/test_registro.py` | Motores y comandos registrados | Sí |
| Hooks y devtools | `tests/test_hooks.py`, `tests/test_handoff.py`, `tests/test_devtools.py` | Hooks de agentes y devtools, ejecutados de verdad | Sí |
| Local | `tests/test_venvs.py` (`@pytest.mark.local`) | Cada venv importa su librería | No (`-m local`) |
| tdd efímero | `tests/tdd/test_<pieza>.py` | Razonar una pieza antes de su test permanente | **Nunca**: el `pre-push` falla si existe |

* Un test nuevo va en el archivo de su área (`tests/test_<área>.py`); crea uno nuevo solo si el área no tiene. Sin mirror 1:1 ni coverage por archivo: no hacen falta aquí.
* Si un cambio de comportamiento es a propósito, las fixtures se regeneran con `uv run python tests/fixtures/generar.py` en un commit aparte.

## 2. Qué mockear

* Nunca la función bajo prueba. Sí: el reloj, la GPU y los motores (los tests de CI no cargan modelos), `subprocess` hacia ffmpeg cuando solo importa el comando armado.
* Lo que depende de un modelo real se verifica con la corrida real y sus mediciones (`verify-before-claiming-done.md`), no con un mock: un mock no dice si el audio suena bien.
* Tests sin red ni descargas: lo que baje un modelo es `local` o no es un test.

## 3. TDD

1. **RED**: el test (o el doctest) primero, con el AC en el nombre (`test_ac2_corta_en_silencio`) o en el docstring; ver que falla por el motivo esperado, no por el setup.
2. **GREEN**: lo mínimo para el verde, con `uv run pytest <archivo>::<test>`.
3. **REFACTOR** con la red en verde; cerrar con `uv run ruff check && uv run ruff format --check && uv run pytest`.
* Un fix de bug empieza con su test de regresión en `tests/test_bugs.py`, rojo con el código actual.
* Un test flaky es un fallo. Nada de `sleep` ni timeouts fijos: espera la señal real.

---
name: tdd-workflow
description: >
  Ciclo Red-Green-Refactor obligatorio de content-studio con pytest y doctests. SIEMPRE invocar ANTES de escribir
  código de implementación de una funcionalidad, un motor, un comando, un parser o un fix en server/src/. NUNCA escribir la
  implementación antes de su test en rojo, y NUNCA responder sobre TDD en este repo solo de memoria:
  .agents/rules/testing.md es la fuente. Usar cuando el usuario diga "TDD", "test primero", "tests primero",
  "rojo verde refactor", "ciclo TDD", "nueva feature", "implementar", "arreglar bug", "fix bug", "test de regresión".
allowed-tools: Read, Glob, Grep, Edit, Write, Bash(uv run pytest:*), Bash(uv run ruff:*)
argument-hint: "<archivo o pieza a implementar>"
---

# TDD workflow — content-studio

Red → Green → Refactor con `uv run pytest`. Regla: `.agents/rules/testing.md`.

## Ciclo

1. **Dónde va el test** (`testing.md` §1): doctest si es una función pura chica; `server/tests/test_<área>.py` si no; `server/tests/test_bugs.py` si es un fix. Si hace falta razonar la pieza antes, `tests/tdd/test_<pieza>.py` (efímero: el `pre-push` lo rechaza).
2. **RED**: escribe el test con el AC en el nombre o el docstring (`test_ac2_...`) y córrelo: `uv run pytest server/tests/test_<área>.py::<test> -q`. Tiene que fallar por el motivo esperado (no por un import o el setup).
3. **GREEN**: lo mínimo para el verde, mismo comando. Nada de lo que ningún AC pide (`plan-format.md` §0).
4. **REFACTOR** con la red en verde; cierra con `uv run ruff check && uv run ruff format --check && uv run pytest`.
5. Si el cambio toca un motor o la salida de audio, el verde de pytest no basta: corrida real con `gpu-turn run` y medición (`verify-before-claiming-done.md`).

## Reglas

- Un fix empieza con un test de regresión que reproduce el bug, rojo con el código actual.
- Nunca mockees la función bajo prueba; los motores y la GPU, sí (la CI no los tiene).
- Si cambia a propósito la salida de los parsers, regenera las fixtures con `uv run python server/tests/fixtures/generar.py` en un commit aparte.
- Convierte o borra los tests de `tests/tdd/` antes del push.

## Salida esperada

En español, citando el archivo de test y el comando exacto de cada fase.

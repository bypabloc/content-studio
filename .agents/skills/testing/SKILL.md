---
name: testing
description: >
  Referencia de testing de content-studio: dónde va cada test (doctest, caracterización, estructura, bugs, CLI,
  hooks, local, tdd efímero), qué se mockea y cómo se corre. SIEMPRE invocar ANTES de crear o mover un test, o de
  responder dónde va un test o cómo se corren. NUNCA responder solo de memoria: .agents/rules/testing.md es la fuente.
  Usar cuando el usuario diga "test", "tests", "pytest", "doctest", "dónde va el test", "mockear", "qué mockeo",
  "fixtures", "caracterización", "tests locales", "-m local", "flaky", "cómo corro los tests".
allowed-tools: Read, Glob, Grep, Bash(uv run pytest:*)
argument-hint: "tipos | mocking | correr | fixtures"
---

# Testing — content-studio

Dónde va cada test, qué mockea y cómo se ejecuta. Fuente: `.agents/rules/testing.md`.

## Comandos

```bash
python -m devtools test-runner --type=all  # lo que corre CI: lint, spelling, tamaño, cobertura, espejo, mypy y tdd
uv run pytest                          # doctests de server/src/, tests/ (sin GPU)
uv run pytest server/tests/integration/test_bugs.py -q    # un archivo
uv run pytest -k ac2 -q                # por nombre
uv run pytest -m local                 # además, los venvs de los motores (solo en este equipo)
uv run python server/tests/integration/fixtures/generate.py  # regenerar fixtures tras un cambio de salida intencional (commit aparte)
```

## Reglas

- Un test por comportamiento, en el archivo de su área; el AC en el nombre.
- Sin red, sin descargas y sin GPU en lo que corre la CI: eso es `@pytest.mark.local` o una verificación real.
- Nunca mockees la función bajo prueba; un mock no dice si el audio suena bien (`verify-before-claiming-done.md`).
- `server/tests/tdd/` y `devtools/tests/tdd/` son efímeros: `guard-tdd` (pre-push y CI) falla si quedan archivos.
- `tests/validators/test_structure.py` hace cumplir `codigo-python.md` y la sincronía `.agents/` ↔ `.claude/`: si falla, corrige el código, no el test.

## Salida esperada

En español, con la ruta exacta del test y el comando.

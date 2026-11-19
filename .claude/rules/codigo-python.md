# Código Python — SIEMPRE ACTIVO

## Dónde vive el código

- Todo el código vive en `server/src/content_studio/`. En la raíz solo queda `cli.py`, que es un shim. La excepción son los hooks de Claude Code en `.claude/hooks/`, con solo stdlib y probados en `.claude/hooks/tests/test_hooks.py`.
- `server/data/narration/` y `server/data/music/` son carpetas de datos: README, docs, voces, catálogo, venvs, `engines/` y `models/`. **No se mueven venvs ni assets**: hacerlo rompe los venvs o dispara descargas de varios GB. Un worktree los enlaza (`worktrees.md`).
- Las herramientas del flujo de agentes viven en `server/src/content_studio/devtools/` (`devtools.md`).

## Reglas

- **Tamaño por categoría** (`tests/validators/file-size.json`): fuente 300 líneas, tests 800. Si un archivo se acerca, se divide por responsabilidad. La etapa `validators` lo exige sin excepciones; el baseline solo puede bajar. `test_structure.py` vigila que no haya `.py` sueltos en la raíz ni en `server/data/`.
- **Python 3.10 como mínimo** (el venv de CosyVoice es 3.10), con `from __future__ import annotations` para escribir `X | None`. Nada de `tomllib`, `Self`, `ExceptionGroup`, `datetime.UTC` ni `match` con sintaxis nueva. CI corre en 3.10 y 3.12.
- **Dos capas.** En el nivel superior de un módulo solo va stdlib, salvo en `cli/` y `grabar/` (typer, rich, questionary). torch, numpy, soundfile y las librerías de cada motor se importan dentro de funciones, así `--help`, los parsers y el catálogo funcionan sin el venv del motor.
- **Factory Method solo con dos o más productos**: motores TTS, motores de música y comandos del CLI. Lo que tiene un solo producto (referencia, catálogo de voces, fuentes, grabar) es una función o un módulo. SOLID y KISS: nada de interfaces, configuración ni autodescubrimiento que hoy no se usen.
- Type hints en las firmas de src (ruff ANN001/ANN201 lo exige; los tests quedan fuera). Comillas simples y 120 columnas (`ruff format`).

## Cómo agregar

- **Un motor TTS o de música**: un archivo en `engines/`, una línea en `engines/registry.py`, su venv y la librería en `LIBRARIES` de `server/tests/integration/test_venvs.py`.
- **Un comando del CLI**: una clase `Comando` y una línea en `REGISTRY`.
- **Un comando de devtools**: un módulo con `main(argv)` y una línea en `COMMANDS` (`devtools.md`).
- Algo de más de dos archivos: primero su spec (`plan-format.md`).

## Antes de cada commit

```bash
uv run ruff check && uv run ruff format --check
python -m devtools test-runner --type=all   # todas las etapas de calidad (spec 003); `uv run pytest -m local` suma los venvs
```

Si un cambio de comportamiento es a propósito, se regeneran las fixtures con `uv run python server/tests/integration/fixtures/generate.py` en un commit aparte.

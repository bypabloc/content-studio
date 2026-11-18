# Código Python — SIEMPRE ACTIVO

## Dónde vive el código

- Todo el código vive en `src/content_studio/`. En la raíz solo queda `cli.py`, que es un shim.
- `narration/` y `music/` son carpetas de datos: README, docs, voces, catálogo, venvs, `motores/` y `models/`. **No se mueven venvs ni assets**: hacerlo rompe los venvs o dispara descargas de varios GB.

## Reglas

- **Máximo 300 líneas por `.py`.** Si un archivo se acerca, se divide por responsabilidad, no por tamaño. Lo comprueba `tests/test_estructura.py`, sin excepciones; también falla si aparece un `.py` fuera de `src/`, `tests/` y `cli.py`.
- **Python 3.10 como mínimo** (el venv de CosyVoice es 3.10), con `from __future__ import annotations` para escribir `X | None`. Nada de `tomllib`, `Self`, `ExceptionGroup` ni `match` con sintaxis nueva. CI corre en 3.10 y 3.12.
- **Dos capas.** En el nivel superior de un módulo solo va stdlib, salvo en `cli/` y `grabar/` (typer, rich, questionary). torch, numpy, soundfile y las librerías de cada motor se importan dentro de funciones, así `--help`, los parsers y el catálogo funcionan sin el venv del motor.
- **Factory Method solo con dos o más productos**: motores TTS, motores de música y comandos del CLI. Lo que tiene un solo producto (referencia, catálogo de voces, fuentes, grabar) es una función o un módulo. SOLID y KISS: nada de interfaces, configuración ni autodescubrimiento que hoy no se usen.
- Type hints en las firmas públicas.

## Cómo agregar

- **Un motor TTS o de música**: un archivo en `motores/`, una línea en `motores/registro.py` y su venv.
- **Un comando del CLI**: una clase `Comando` y una línea en `REGISTRO`.

## Antes de cada commit

```bash
uv run ruff check && uv run ruff format --check
uv run pytest            # doctests, caracterización, estructura y bugs; -m local corre los de los venvs
```

Si un cambio de comportamiento es a propósito, se regeneran las fixtures con `uv run python tests/fixtures/generar.py` en un commit aparte.

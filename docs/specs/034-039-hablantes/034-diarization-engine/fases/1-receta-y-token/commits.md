# Spec 034, fase 1: commit

Una fase es un grupo de commit: deja verdes ruff y pytest de su changeset.

## Mensaje

```text
feat: receta de pyannote y token de Hugging Face en la instalación

- familia diarization y paso hf con gated (HF_TOKEN solo en su entorno)
- exit 25 engine_gated cuando Hugging Face niega el acceso
```

El tipo coincide con el prefijo de la rama (`git-workflow.md`); sin atribución de IA.

## Gate del grupo

```bash
uv run ruff check && uv run ruff format --check
uv run pytest
bun run --cwd client test   # si la fase toca el client
```

Nunca por grupo: lo que carga un modelo, `pytest -m local`, e2e ni la validación headless (van en la verificación final).

## Al cerrar la fase

- [ ] Fila de la fase en el README con su commit y estado `IMP`; filas de la matriz de verificación marcadas.
- [ ] Fichas WARNING/PENDING que surgieron en esta fase, en este mismo commit.

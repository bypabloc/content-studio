# Spec 031, fase 1: commit

Una fase es un grupo de commit: deja verdes ruff y pytest de su changeset.

## Mensaje

```text
feat: enlaces content-studio:// que abren y prellenan sin encolar

- deep-link y single-instance de tauri
- lista blanca de acciones y parámetros en una función pura
```

El tipo coincide con el prefijo de la rama (`git-workflow.md`); sin atribución de IA.

## Gate del grupo

```bash
uv run ruff check && uv run ruff format --check
uv run pytest
python -m devtools test-runner --type=tauri-check
bun run --cwd client test
```

Nunca por grupo: lo que carga un modelo, `pytest -m local`, e2e ni la validación headless (van en la verificación final).

## Al cerrar la fase

- [ ] Fila de la fase en el README con su commit y estado `IMP`; filas de la matriz de verificación marcadas.
- [ ] Fichas WARNING/PENDING que surgieron en esta fase, en este mismo commit.

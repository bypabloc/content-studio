# Spec 027, fase 1: commit

Una fase es un grupo de commit: deja verdes ruff y pytest de su changeset.

## Mensaje

```text
chore: dependencias de javascript en su última versión

- client, e2e y raíz con versiones exactas al día
- adaptaciones de API que pidieron las versiones nuevas
```

El tipo coincide con el prefijo de la rama (`git-workflow.md`); sin atribución de IA.

## Gate del grupo

```bash
uv run ruff check && uv run ruff format --check
uv run pytest
bun run --cwd client typecheck && bun run --cwd client test
```

Nunca por grupo: lo que carga un modelo, `pytest -m local`, e2e ni la validación headless (van en la verificación final).

## Al cerrar la fase

- [ ] Fila de la fase en el README con su commit y estado `IMP`; filas de la matriz de verificación marcadas.
- [ ] Fichas WARNING/PENDING que surgieron en esta fase, en este mismo commit.

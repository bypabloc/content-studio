# Spec 034, fase 3: commit

Una fase es un grupo de commit: deja verdes ruff y pytest de su changeset.

## Mensaje

```text
feat: token de Hugging Face y atribución de pyannote en la app

- grupo Diarización en Motores con el campo del token y el enlace a las condiciones
- atribución CC-BY-4.0 de community-1 en Acerca de
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

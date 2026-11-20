# 010: el worktree no trae el grupo legacy

- **Qué queda**: en un worktree nuevo, `uv run pytest` no importa `grabar/` porque faltan `questionary` y `rich`, que son del grupo `legacy` de `server/pyproject.toml`. La colección de doctests falla hasta correr `uv sync --all-packages --all-groups`. Se vio al cerrar el ciclo 1: el `.venv` del worktree no existía antes de la primera corrida.
- **Cuándo**: con la T8, que borra `grabar/` y el grupo `legacy`.
- **Revisar**: si `python -m devtools worktree prepare` debe dejar el `.venv` con todos los grupos. Hoy no se comprobó qué instala.

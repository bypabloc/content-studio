# Worktrees de trabajo: dónde van y cómo se crean — SIEMPRE ACTIVA

> Un worktree por tarea, todos **junto al repo** en `../content-studio-worktrees/`. Dentro del repo, una sesión abierta en el principal cargaría las reglas del worktree como reglas anidadas, duplicadas (en klinikae, ~30k tokens más por compactación).

## Regla dura

* **SIEMPRE** en `../content-studio-worktrees/<nombre>/`, al lado del checkout principal. `<nombre>` es la spec o el tema, sin prefijo `wt-`.
* **SIEMPRE** desde `origin/dev`, con una rama de trabajo con prefijo válido (`git-workflow.md`).
* **NUNCA** dentro del repo (`.worktrees/`, `tmp/`, `.claude/worktrees/`). En Claude Code, `.claude/hooks/worktree_guard.py` lo bloquea. `claude --worktree` y `EnterWorktree` crean en `.claude/worktrees/` desde la rama por defecto (`main`): para trabajo de `dev` usa el comando de abajo.
* **NUNCA** `dev` ni `main` como worktree.

## Crear y preparar

```bash
git fetch origin dev
git worktree add ../content-studio-worktrees/<nombre> -b <prefijo>/<nombre> origin/dev
python -m devtools worktree prepare <nombre>     # desde el checkout principal
```

`git worktree add` solo trae lo versionado: no hay venvs (`server/data/narration/.venv-*`, `server/data/music/.venv-*`), repos de motores (`server/data/narration/engines/`), modelos (`server/data/music/models/`), voces construidas (`server/data/narration/voices/<voz>/`) ni audios de referencia (`server/data/narration/reference/*.wav`). Pesan GB y no se mueven (`codigo-python.md`), así que `prepare` **enlaza** las carpetas al principal (symlink en POSIX, junction en Windows) y copia los audios que faltan, sin pisar nada, y crea `tmp/`. Así el worktree corre motores igual que el principal. Después, `uv sync` en el worktree para el venv de desarrollo.

`.claude/settings.json` declara `../content-studio-worktrees` en `permissions.additionalDirectories`: una sesión del principal lee y edita ahí sin pedir permiso.

## Cerrar (obligatorio tras el merge)

Al fusionar el PR a `dev`, ciérralo en el mismo cierre, sin pedir permiso y desde el checkout principal:

```bash
git fetch origin dev
python -m devtools worktree close <nombre> [--handoff=<trabajo>]
```

Exige su HEAD en `origin/dev` y el árbol limpio (exit 1 si no). En orden: quita los enlaces de `prepare` (para que `git worktree remove` no entre en los venvs del principal), `git worktree remove` y `prune`, borra la rama local y la remota, y borra su handoff (`tmp/handoff/<trabajo>/`, por defecto `<nombre>`) y sus vínculos. No des el trabajo por cerrado mientras `git worktree list` lo muestre.

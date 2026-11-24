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

`git worktree add` trae solo lo versionado. `prepare` **enlaza** los venvs y modelos desde el `paths.engines_dir()` efectivo del principal.
También enlaza voces, referencias y audios desde `server/data/`, copia los audios que faltan y crea `tmp/`.
No asume que los motores viven dentro del checkout.
Corre `bun install` (no enlaza `node_modules`: `bun` escribiría en el principal) y luego `uv sync`.
El target de Cargo va a `<principal>/tmp/cargo-target`; si ya existe, no se toca.

`.claude/settings.json` declara `../content-studio-worktrees` en `permissions.additionalDirectories`: una sesión del principal lee y edita ahí sin pedir permiso.

## Cerrar (obligatorio tras el merge)

Al fusionar el PR a `dev`, ciérralo en el mismo cierre, sin pedir permiso y desde el checkout principal:

```bash
git fetch origin dev
python -m devtools worktree close <nombre>
```

Exige su HEAD en `origin/dev` y el árbol limpio (exit 1 si no). Quita los enlaces de `prepare` (para que `git worktree remove` no entre en los venvs del principal), hace `git worktree remove` y `prune` (en Windows, si la carpeta sigue retenida, avisa y sigue) y borra la rama local y la remota. No des el trabajo por cerrado mientras `git worktree list` lo muestre.

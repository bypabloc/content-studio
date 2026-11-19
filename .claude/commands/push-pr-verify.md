---
description: Push de la rama actual, PR idempotente y verificación de checks (sin merge)
allowed-tools: Read, Bash(git:*), Bash(gh:*), Bash(uv run:*)
argument-hint: "[rama-base] (default: dev; main solo para fix/* de hotfix)"
---

# /push-pr-verify

1. **Pre-checks**: `git status` limpio y rama de trabajo con prefijo válido (`.claude/rules/git-workflow.md`). Si hay cambios sin confirmar, detente y avisa.
2. **Base**: `$ARGUMENTS` o `dev`. `main` solo acepta `dev` y `fix/*`.
3. **Push**: `git push -u origin <rama>`. Si el `pre-push` falla, corrige la causa; nunca `--no-verify`.
4. **PR idempotente**: `gh pr list --head <rama> --state open`. Si existe, el push ya lo actualizó. Si no, `gh pr create --base <base>` con:
   - Título en Conventional Commits en español, con el tipo igual al prefijo de la rama.
   - Cuerpo desde `git log --oneline <base>..HEAD` y `git diff --stat <base>...HEAD`: **Problema**, **Solución** (archivos clave `ruta — qué hace`), **Cómo probar** (comandos reales: `uv run pytest`, `uv run studio ...` y la ruta de salida en `out/`) y lo verificado en esta sesión.
5. **Checks**: `gh pr checks <rama> --watch` (`origen-permitido` y `calidad`).
6. **Reporte**: URL del PR, estado de cada check y, si alguno falló, `gh run view --log-failed`.

Prohibido: atribución de IA en título o cuerpo, `--no-verify` y hacer merge sin que el usuario lo pida.

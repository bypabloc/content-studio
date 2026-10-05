# Git workflow — SIEMPRE ACTIVO

Repo: `bypabloc/content-studio` (público). Remoto por SSH con el alias de la cuenta personal:
`git@github.com-personal:bypabloc/content-studio.git`. **No** uses `git@github.com:`, porque esa clave
es la de otra cuenta y el push falla con "Could not read from remote repository".

## Ramas

| Rama | Rol | Acepta PRs desde |
|---|---|---|
| `main` | Lo estable y publicado | `dev` y `fix/*` (hotfix) |
| `dev` | Integración | `main` (back-merge) y las ramas de trabajo con prefijo |

**Nunca** se hace push directo a `main` ni a `dev`. Todo cambio entra por pull request.

## Prefijos de ramas de trabajo (siempre se crean desde `dev`)

| Prefijo | Uso |
|---|---|
| `feature/` | Funcionalidad nueva |
| `fix/` | Corrección de bug (puede ir a `dev` o, como hotfix, directo a `main`) |
| `refactor/` | Reestructuración sin cambio de comportamiento |
| `docs/` | Solo documentación (README, guiones) |
| `test/` | Agregar o ajustar pruebas |
| `chore/` | Mantenimiento: dependencias, configuración, `.gitignore` |
| `ci/` | Workflows y rulesets |
| `perf/` | Rendimiento (VRAM, velocidad) |
| `style/` | Formato sin cambios de lógica |
| `experiment/` | Pruebas exploratorias (por ejemplo, un modelo nuevo) |
| `release/` | Preparar una versión antes de pasar a `main` |

El separador `/` es obligatorio y después del prefijo tiene que venir un nombre en kebab-case: `feature/musica-cinematic`. Una rama sin prefijo válido no puede mergear (el check falla).

## Flujo

```bash
git switch dev && git pull
git switch -c feature/<nombre>
# ... commits ...
git push -u origin feature/<nombre>
gh pr create --base dev --title "feat: ..." --body "..."
gh pr merge --merge --delete-branch          # cuando el check pase

# Publicar: PR de dev a main
gh pr create --base main --head dev --title "release: ..." --body "..."

# Hotfix: fix/* desde main → PR a main. La sincronización a dev es automática (ver abajo)
git switch main && git pull && git switch -c fix/<nombre>
gh pr create --base main --title "fix: ..." --body "..."
```

**Sincronización automática main → dev**: cada push a `main` (el merge de un `fix/*` o de `dev`) dispara el workflow [.github/workflows/sync-dev.yml](../../.github/workflows/sync-dev.yml). Si `dev` está atrasada, el workflow abre el PR `main → dev` y lo deja en auto-merge, así que se mergea solo cuando pasa `origen-permitido`. **No abras ese PR a mano.** Si hay conflicto, el PR queda abierto: resuélvelo en una rama `fix/` desde `dev` o directamente en el PR. Usa el secret `SYNC_TOKEN` (token fine-grained con Contents y Pull requests en read/write): si vence, la sincronización falla con un error de autenticación y hay que renovar el token y el secret.

## Qué lo hace cumplir (en GitHub, no solo esta regla)

- **Ruleset `proteger-main-dev`** (main y dev): exige PR, bloquea force-push y borrado. Sin excepciones, ni siquiera para administradores.
- **Ruleset `main-solo-desde-dev-o-fix`** (main) y **`dev-solo-desde-prefijos`** (dev): exigen que pase el check `origen-permitido`.
- **Workflow [.github/workflows/origen-pr.yml](../../.github/workflows/origen-pr.yml)**: es el check `origen-permitido`. Valida la rama de origen según el destino y rechaza los PRs de forks. **Si cambias los prefijos, cambia la lista `PREFIJOS_DEV` en el workflow y la tabla de esta regla.**
- **Workflow [.github/workflows/sync-dev.yml](../../.github/workflows/sync-dev.yml)**: tras cada push a `main`, abre el PR `main → dev` en auto-merge (el repo tiene activado *Allow auto-merge*).

## Commits y PRs

- Conventional Commits: `feat:`, `fix:`, `refactor:`, `docs:`, `test:`, `chore:`, `ci:`, `perf:`, `style:`. El tipo coincide con el prefijo de la rama.
- **Sin atribución de IA** en commits, PRs ni comentarios (nada de `Co-Authored-By: Claude`, "Generated with…", etc.).
- Antes de confirmar cambios: correr los doctests (`python3 -m doctest music/musica.py narration/tts.py`) y no incluir nada de `out/`, `logs/`, `tmp/`, `models/` ni `.venv-*` (están gitignoreados).
- Commit, push y merge solo cuando el usuario lo pida.

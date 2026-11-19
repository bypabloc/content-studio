# 001: verificación final

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación. Cada una queda en [`docs/process/WARNING/`](../../../process/WARNING/README.md); toda revisión pendiente, en [`docs/process/PENDING/`](../../../process/PENDING/README.md).
>
> **Datos del usuario: solo los que crea esta spec**. No borra ni sobrescribe voces grabadas, voces construidas, salidas de `out/` ni modelos que no creó; si algo parece exigirlo, es un `blocked — user-data`. Excepción pedida: `move-data` mueve `narration/` y `music/` a `server/data/`.

Una sola vez, con todos los commits hechos y antes del push. Si algo falla, se corrige con commits `fix(...)` y se repite solo lo rojo.

## 1. Batería (en el worktree)

1. `uv run ruff check && uv run ruff format --check`
2. `uv run pytest`. El total de `-q --co` tiene que ser igual a la base anotada en el handoff (AC-1).
3. `python -m devtools --help`, un caso real (`python -m devtools move-data`, sin `--apply`, sobre el principal: imprime el plan) y un caso de error (`python -m devtools move-data --foo` sale con exit 2).
4. `python -m devtools contexto-agentes` y `python -m devtools reglas`, más la validación headless de `agent-config-testing.md`.
5. `python cli.py --help | cat` y `python cli.py narration tts --help | cat`: no deben preguntar nada.

## 2. Migración real (en el principal, antes del merge)

La migración solo se puede probar en el principal, que es donde están los datos. El orden protege los datos:

1. `git -C <principal> status`: el árbol tiene que estar limpio. Anota en el handoff el tamaño de `narration/` y `music/` (`du -sh`) y la cantidad de `.wav` en `narration/voz/`.
2. Desde el worktree: `python -m devtools move-data` (por defecto apunta al principal, con `worktree.principal()`, o a `--root <ruta>`) imprime el plan. Revísalo. La migración se aplica **justo antes del merge** porque, mientras el principal siga en el `dev` viejo, sus rutas quedan rotas: `move-data --apply`, merge del PR y `git pull` en el principal, todo seguido (§5).
3. `python -m devtools move-data --apply`.
4. Comprueba que el tamaño y la cantidad de `.wav` en `server/data/` coincidan con lo anotado y que `narration/` y `music/` ya no existan.
5. `uv run pytest -m local` (AC-5).
6. Corrida real con el turno (AC-6):
   * `python -m devtools turno-gpu run --trabajo=001-server-devtools -- python cli.py narration tts --modelo qwen-0.6b --voz yesid --texto "Prueba de la spec uno." --salida out/narration/spec-001/`
   * `python -m devtools turno-gpu run --trabajo=001-server-devtools -- python cli.py music --modelo acestep --estilo lofi-chill --duracion 15 --carpeta out/music/spec-001/`
7. Mide la duración de cada salida (`ffprobe`, `verify-before-claiming-done.md` §2). La música tiene que durar 15 s ± 0,5 s y la narración tiene que ser mayor que 0. No cambia ningún audio, así que no hace falta espectrograma.

**Cómo revertir** (va en `WARNING/001-move-data.md`): `git switch dev` y `os.replace` inverso (`server/data/narration` → `narration`, `server/data/music` → `music`), más la misma reescritura de los `.pth` en sentido contrario. Se puede agregar un `move-data --revert` si cuesta menos que documentarlo; decídelo al implementar.

## 3. Escucha

Las salidas de `out/narration/spec-001/` y `out/music/spec-001/` van en el reporte. No hay que elegir entre opciones sonoras, así que la escucha no bloquea nada.

## 4. Cierre

* No es una spec funcional, así que no toca `01-done/` salvo para corregir rutas (ciclo 7).
* `docs/process/WARNING/001-move-data.md` con su fila en el README.
* La carpeta del lote **no** se borra aquí: la borra la 016. Al terminar, se actualiza el estado de la fila 001 en `docs/specs/001-017-studio/README.md`.

## 5. PR y merge

1. `git fetch origin dev` y merge de `origin/dev` si avanzó; un solo push.
2. `gh pr list --head refactor/001-server-devtools`. Si no existe, `gh pr create --base dev` con el problema, la solución, cómo probar y los pasos de `move-data` para cualquier otro checkout, y enlaza la ficha WARNING.
3. `gh pr checks <n> --watch`. Con todo verde, `gh pr merge <n> --merge`.
4. En el principal: `git switch dev && git pull`. Comprueba que `server/data/` siga intacto y cierra con `python -m devtools worktree close 001-server-devtools`.

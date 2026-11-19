# 002: verificación final

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación. Cada una queda en [`docs/process/WARNING/`](../../../process/WARNING/README.md); toda revisión pendiente, en [`docs/process/PENDING/`](../../../process/PENDING/README.md).
>
> **Datos del usuario: solo los que crea esta spec**. No borra ni sobrescribe voces grabadas, voces construidas, salidas de `out/` ni modelos que no creó; si algo parece exigirlo, es un `blocked — user-data`. Excepción pedida: `move-data` renombra datos a inglés.

## 1. Batería (en el worktree)

1. `uv run ruff check && uv run ruff format --check`
2. `uv run pytest`
3. `python -m devtools spelling`, que tiene que dar `{"issues": 0}` (AC-1).
4. `python -m devtools agent-context` y `python -m devtools rules`, más la validación headless de `agent-config-testing.md` (AC-9).
5. `python cli.py narration tts --help | cat`, `python cli.py music --help | cat` y `python cli.py music --modelo acestep`, que tiene que salir con exit 2 (AC-6).
6. Prueba del gate: un commit de prueba con `def calcular_total(): ...` se rechaza (AC-3). Después se descarta con `git reset` y no se hace push.

## 2. Migración real y corridas (en el principal, justo antes del merge)

1. Árbol limpio. Anota en el handoff la cantidad y los bytes de `server/data/narration/voz/**` y `voces/**`.
2. `python -m devtools move-data` (plan), revisión y después `python -m devtools move-data --apply`.
3. La cantidad y los bytes en `reference/**` y `voices/**` coinciden con lo anotado. `voz/`, `voces/` y `motores/` ya no existen (AC-4).
4. `uv run pytest -m local` (AC-8).
5. Con el turno:
   * `python -m devtools gpu-turn run --task=002-english-cspell -- python cli.py narration tts --model qwen-0.6b --style expert --voice yesid --text "Prueba de la spec dos. [pausa 0.5] Con alias." --output out/narration/spec-002/`
   * `python -m devtools gpu-turn run --task=002-english-cspell -- python cli.py music --model acestep --style lofi-chill --duration 15 --folder out/music/spec-002/`
6. Duración y LUFS de las dos salidas (`verify-before-claiming-done.md` §2), contra «debe sonar» de `01` §7. Espectrograma de la música en `tmp/spec-002/spec.png`, que revisa `image-reader` (sin formantes de voz).

## 3. Escucha

Las rutas de `out/narration/spec-002/` y `out/music/spec-002/` van en el reporte. No hay que elegir entre opciones.

## 4. Cierre

* Fichas `WARNING/002-mapeo-de-nombres.md` y `PENDING/002-cspell-excepciones-temporales.md` con sus filas.
* `docs/process/01-done/` con los flags y rutas nuevos.
* Estado de la fila 002 en `docs/specs/001-017-studio/README.md`. La carpeta del lote la borra la 016.

## 5. PR y merge

1. `git fetch origin dev` y merge si avanzó; un solo push.
2. PR a `dev` si no existe, con la tabla de renombres, los pasos de `move-data` para otros checkouts y las fichas.
3. `gh pr checks <n> --watch` (incluye el paso nuevo de spelling) y `gh pr merge <n> --merge`.
4. En el principal: `git switch dev && git pull` y `python -m devtools worktree close 002-english-cspell`.

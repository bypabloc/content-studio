# 005: verificación final

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación. Cada una queda en [`docs/process/WARNING/`](../../../process/WARNING/README.md); toda revisión pendiente, en [`docs/process/PENDING/`](../../../process/PENDING/README.md).
>
> **Datos del usuario: solo los que crea esta spec**. No borra ni sobrescribe voces grabadas, voces construidas, salidas de `out/` ni modelos que no creó; si algo parece exigirlo, es un `blocked — user-data`.

## 1. Batería

1. `python -m devtools test-runner --type=all` (Python y client), `--type=e2e`, `--type=tauri-check` y `--type=budget` (AC-9).
2. `python -m devtools spelling` (AC-8).
3. `python -m devtools agent-context` y `rules`, más la validación headless.

## 2. App real

1. `bun run --cwd client tauri dev` (en segundo plano, con el log en `logs/client-spec-005.log`). La ventana «Content Studio» abre sin consola extra (AC-1).
2. Desde la UI, encola dos trabajos de música de 15 s con `studio` en otra terminal (todavía no hay sección Música), con el turno: `python -m devtools gpu-turn run --task=005-client-base -- uv run studio music --model acestep --style lofi-chill --duration 15`. Comprueba en la cola el progreso en vivo, el toast, la notificación de Windows con la ventana minimizada y el sonido.
3. Cambia el tema a oscuro, claro y sistema. Cambia el tema de Windows con la app en `system` (AC-2). Cierra y reabre la app: no hay parpadeo.
4. Cierra la ventana y corre `tasklist | findstr /i "studio uvicorn python"`: no queda ningún proceso del server (AC-1).
5. Con `uv` renombrado de forma temporal en el PATH de la sesión de prueba (sin tocar el sistema: `PATH` sin la carpeta de uv), la app muestra el error y el botón Reintentar (AC-10).
6. Capturas en `tmp/spec-005/` (shell en claro y en oscuro, la cola con progreso y Ajustes), que revisa `image-reader`: contraste legible, el acento violeta presente y nada cortado a 960×640.

## 3. Revisión visual

Las capturas de `tmp/spec-005/` van en el reporte para que el usuario las vea. Si pide cambios de gusto (tonos o espaciados), se hacen en esta misma spec antes del PR.

## 4. Cierre

* `docs/process/01-done/` con la ficha nueva `client.md`.
* Fichas WARNING `005-tanstack-query.md` y `005-ci-windows-rust.md`.
* Estado de la fila 005 en el README del lote.

## 5. PR y merge

1. `git fetch origin dev` y merge si avanzó; un solo push.
2. PR a `dev` si no existe, con capturas, cómo abrir la app, las etapas nuevas y las fichas.
3. `gh pr checks <n> --watch` (con los jobs `client` y `tauri`) y `gh pr merge <n> --merge`.
4. En el principal: `git switch dev && git pull`, `bun install` y `python -m devtools worktree close 005-client-base`.

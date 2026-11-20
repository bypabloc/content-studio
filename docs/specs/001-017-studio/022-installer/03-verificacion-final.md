# 022: verificación final

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación. Cada una queda en [`docs/process/WARNING/`](../../../process/WARNING/README.md); toda revisión pendiente, en [`docs/process/PENDING/`](../../../process/PENDING/README.md).
>
> **Datos del usuario: solo los que crea esta spec**. No borra ni sobrescribe voces grabadas, voces construidas, salidas de `out/` ni modelos que no creó; si algo parece exigirlo, es un `blocked — user-data`. Cargar el secret de GitHub requiere la aprobación del usuario.

## 1. Batería

1. `python -m devtools test-runner --type=all`, `--type=e2e`, `--type=tauri-check` y `--type=guard-tdd`.
2. `cargo test` en `client/src-tauri`.
3. `python -m devtools version --check`, más un caso real (`version 0.1.0`) y uno de error (`version 1.2`, exit 2).

## 2. Instalación real (en un usuario o carpeta de prueba)

1. `python -m devtools fetch-uv` y `bun run --cwd client tauri build`, en segundo plano, con el log en `logs/client-build-spec-022.log`. Comprueba el tamaño del `.exe` (< 60 MB) y lista el contenido de los recursos (AC-6).
2. Instala en un usuario de Windows de prueba (o, si no hay uno, con `CONTENT_STUDIO_HOME` apuntando a `tmp/spec-022/home/` y sin uv ni Python en el PATH de la sesión). No pide administrador. En el primer arranque aparece la pantalla de preparación con el progreso, y después la bienvenida (AC-7).
3. Desde la bienvenida, instala Qwen 0.6B (con el turno de GPU para la verificación) y genera una narración corta. Comprueba la duración.
4. Cierra y reabre: el bootstrap no repite pasos.
5. Desinstala sin la casilla: los datos quedan. Reinstala: los datos siguen y no se vuelven a sembrar los modificados. Desinstala con la casilla: se borran solo los datos de prueba (AC-8).
6. **Updater** (AC-9): compila la versión 0.1.1 con la misma clave, sirve un `latest.json` firmado desde un servidor local (`python -m http.server` en `tmp/spec-022/update/`, con el endpoint del build de prueba apuntando a localhost). La 0.1.0 instalada ofrece actualizar, espera a que no haya trabajos y se actualiza.
7. **Release**: corre `release.yml` en `workflow_dispatch` `dry-run` (AC-10). El primer Release real (`v0.1.0`) **no** se publica en esta spec sin la aprobación del usuario: se deja listo y se pregunta en el cierre del lote (023).
8. Capturas de la pantalla de preparación, la bienvenida y Ajustes > Acerca de en `tmp/spec-022/`, que revisa `image-reader`.

## 3. Credenciales

* `tauri signer generate -w ~/.tauri/content-studio.key` (fuera del repo). La `pubkey` va a `tauri.conf.json`.
* Cargar `TAURI_SIGNING_PRIVATE_KEY` y su contraseña con `gh secret set` **solo con la aprobación del usuario**. Sin ella, `Status: blocked — credentials` para el paso de release real, y el resto de la spec sigue.

## 4. Cierre

* `docs/process/01-done/installer.md`, nueva, y `docs/operations/release.md`.
* Fichas WARNING `022-recursos-empaquetados.md` y `022-smartscreen.md`, y PENDING `022-firma-de-codigo.md`.
* Se borra `tmp/spec-022/`.
* Estado de la fila 022 en el README del lote.

## 5. PR y merge

1. `git fetch origin dev` y merge si avanzó; un solo push.
2. PR a `dev` si no existe, con el tamaño del instalador, las capturas, los pasos de release y las fichas.
3. `gh pr checks <n> --watch` y `gh pr merge <n> --merge`.
4. En el principal: `git switch dev && git pull` y `python -m devtools worktree close 022-installer`.

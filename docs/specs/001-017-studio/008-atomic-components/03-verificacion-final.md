# 008: verificación final

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación. Cada una queda en [`docs/process/WARNING/`](../../../process/WARNING/README.md); toda revisión pendiente, en [`docs/process/PENDING/`](../../../process/PENDING/README.md).
>
> **Datos del usuario: solo los que crea esta spec**. No borra ni sobrescribe voces grabadas, voces construidas, salidas de `out/` ni modelos que no creó; si algo parece exigirlo, es un `blocked — user-data`.

Una sola vez, con todos los commits hechos y antes del push. No carga modelos: no pide turno de GPU.

## 1. Batería

1. `uv run ruff check && uv run ruff format --check`.
2. `python -m devtools test-runner --type=all`, que ya incluye `ui-structure` e `i18n`.
3. `python -m devtools test-runner --type=e2e` y `--type=budget`. El PR anota el delta del bundle inicial y la lista de chunks diferidos (AC-9).
4. `python -m devtools test-runner --type=ui-structure --git-mode=all` y `--type=i18n --git-mode=all`, los dos con 0 hallazgos.
5. `python -m devtools rules` y `python -m devtools agent-context`, más la validación headless de `agent-config-testing.md`.
6. Inventario: `inventory.test.ts` en verde, y el PR lista los 69 componentes por nivel.

## 2. Pre-commit real (AC-4)

En el worktree, en una rama temporal `test/008-precommit` que se borra al terminar:

1. Pon un `<div>` en `features/settings/SettingsPage.tsx` y haz `git add` y `git commit`. El hook lo rechaza con la línea de AC-2.
2. Importa `shadcn/button` desde `features/queue/JobRow.tsx`. El hook lo rechaza con `no-restricted-imports`.
3. Haz que un átomo importe una molécula. El hook lo rechaza.
4. Revierte los tres cambios. Las salidas quedan en `tmp/spec-008/precommit-<caso>.log` y van al PR.

## 3. App real

1. `bun run --cwd client tauri dev`. Recorre el shell: colapsa la sidebar con el botón y con `Ctrl+B`, mira los tooltips, reinicia y comprueba que sigue colapsada.
2. Prueba la paleta (`Ctrl+K`), la cola (reordenar, cancelar, reintentar), Ajustes (tema, idioma y restablecer) y una narración corta. La narración la encola studio y toma el candado sola (`turno-gpu.md`).
3. Toma capturas del shell expandido y colapsado, la cola con trabajos, Ajustes y Narración, en claro y en oscuro, en `tmp/spec-008/`. Las revisa `image-reader`: sin estilos rotos (clases de tokens sin definir), foco visible, contraste legible y sin desbordes.

## 4. Cierre

* Fichas WARNING `008-base-ui-shadcn.md`, `008-excluidos-de-klinikae.md`, `008-ui-box.md`, `008-tokens-adaptados.md`, `008-appshell.md`, `008-paquete-cn.md` y `008-budget.md`, con su fila.
* Ficha PENDING `008-sincronizar-con-klinikae.md`. Qué la cierra: una decisión del usuario entre seguir copiando a mano, con un script de diff contra klinikae, o un paquete compartido.
* En `PENDING/005-desvios-d1-d8.md`: se cierra el punto 1, porque ya hay componentes de shadcn copiados.
* `docs/process/01-done/client.md`: «Qué hace hoy» (Atomic Design, componentes, AppShell y bloqueo) y «Dónde vive» (`shared/components/{shadcn,atoms,molecules,organisms}`, `shared/forms`, `styles/` y la etapa `ui-structure`).
* El último commit hace `git rm -r docs/specs/001-017-studio/008-atomic-components/`, quita su fila de `docs/specs/README.md` y marca la 008 en el README del lote.

## 5. PR y merge

1. `git fetch origin dev` y merge si avanzó. Un solo push.
2. PR a `dev` si no existe, con el problema, la solución, cómo probar (§1 a §3), el delta del budget, el inventario y las fichas.
3. `gh pr checks <n> --watch` y, con todo verde, `gh pr merge <n> --merge`.
4. En el principal: `git switch dev && git pull` y `python -m devtools worktree close 008-atomic-components`.

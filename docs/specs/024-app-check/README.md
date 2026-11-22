# 024: verificar la app real con `devtools app-check` y prohibir Computer Use

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación.
> Cada una queda anotada en [`docs/process/WARNING/`](../../process/WARNING/README.md) (ficha `024-<tema>.md` con contexto, elegida, descartadas, cómo revertir y cómo comprobarla, y su fila en el README de la carpeta).
> Toda revisión pendiente queda en [`docs/process/PENDING/`](../../process/PENDING/README.md) (ficha y fila, con qué la cierra).
>
> **Datos del usuario: solo los que crea esta spec**. La spec no borra ni sobrescribe voces grabadas (`server/data/narration/voz/`), voces construidas, salidas de `out/` ni modelos descargados que ella no creó. Sus pruebas escriben en carpetas nuevas (`tmp/app-check/` o `tmp/spec-024/`). Si algo parece exigir tocar datos existentes, no se decide al ejecutar: es un `blocked — user-data` y se pregunta. Los cambios locales o sin rastrear del checkout principal no son de la spec: no se tocan y no bloquean.

| Campo | Valor |
| :--- | :--- |
| Tipo | feature |
| Escala | Large (unos 20 archivos entre código, tests, hooks y reglas; 8 ciclos TDD) |
| Rama | `feature/024-app-check` desde `origin/dev`, en `../content-studio-worktrees/024-app-check/` |
| Depende de | ninguna |
| Origen | Pedido del usuario (22-11-2026): Codex verifica la app con Computer Use y falla demasiado |

## Objetivo

Que cualquier agente (Claude Code, Codex y Antigravity) verifique la app de escritorio real con un solo comando, `python -m devtools app-check run`. El comando compila el binario del worktree, lo abre aislado y lo maneja con Playwright por CDP contra el server real, sin tocar el mouse ni el teclado del usuario, y deja capturas y un informe en `tmp/app-check/`. Computer Use queda prohibido en este repo, con un hook que lo bloquea en los tres agentes.

## Índice

* [01-contexto-y-decision.md](01-contexto-y-decision.md): contexto (las fallas medidas), decisiones, fuera de alcance, AC y diagrama.
* [02-plan.md](02-plan.md): ciclos TDD, archivos, tareas y commits.
* [03-verificacion-final.md](03-verificacion-final.md): batería, corrida real, validación de agentes, cierre y PR.

## Fases

| Fase | Qué | Estado |
| :--- | :--- | :--- |
| 0 | Sondeo: CDP de WebView2 en Tauri y nombres de herramientas y eventos de hooks de cada agente (T1) | IMP |
| 1 | Hook `computer_use_guard` y su cableado en los tres agentes (T2–T3) | IMP |
| 2 | `devtools app-check`: entorno aislado, compilación, arranque, espera de CDP y cierre (T4–T6) | IMP |
| 3 | Escenarios de Playwright por CDP: `smoke`, diálogo simulado y modo `real` de solo lectura (T7–T8) | PEN |
| 4 | Reglas, skill y `AGENTS.md`; validación de los tres agentes (T9) | PEN |

## Decisiones clave

* D-1: Playwright por CDP contra el WebView2 real, no Computer Use ni `tauri-driver`: es determinista, no usa el escritorio y reutiliza los helpers de `tests/e2e/support/`.
* D-2: Un binario por worktree con `tauri build --debug --no-bundle` y `CARGO_TARGET_DIR` propio: `project_root()` se fija al compilar (`env!("CARGO_MANIFEST_DIR")`), así que el target compartido abre el server de otro worktree.
* D-3: Aislamiento por corrida: `WEBVIEW2_USER_DATA_FOLDER`, `CONTENT_STUDIO_HOME`, `CONTENT_STUDIO_DB` y un puerto de CDP libre, todo bajo `tmp/app-check/<run>/`.
* D-4: Modo `--data=real`: copia de la base del usuario con la cola en pausa y Playwright aborta todo método distinto de GET.
* D-5: Cierre con un Job Object de Windows (ctypes, stdlib): mueren solo los procesos de la corrida, aunque devtools termine mal.
* D-6: Diálogos nativos simulados envolviendo `__TAURI_INTERNALS__.invoke` solo para `plugin:dialog|open` y `plugin:dialog|save`.
* D-7: Un hook compartido `.agents/hooks/computer_use_guard.py`, cableado en `.claude/settings.json`, `.codex/hooks.json` y `.agents/hooks.json`, y además los plugins de Computer Use desactivados en `.codex/config.toml`.

## WARNING y PENDING

* WARNING: `024-cdp-webview2` (cómo se abre el puerto de CDP), `024-hooks-por-agente` (qué evento y qué herramienta bloquea cada agente), `024-target-por-worktree` (compilación propia frente al target compartido).
* PENDING: ninguna propia. `content-studio.exe` ya no está permitido: `~/.codex/computer-use/config.toml` quedó con `allowed = []` (22-11-2026, a pedido del usuario, que lo borra a mano). Las fichas de revisión visual que `app-check` destraba (`008-revision-visual-organismos`, `012-instalar-motor-real`, `014-capturas-editor`, `015-escucha-y-revision`) se cierran en su propio PR, no en esta spec.

# 005: client Tauri base (shell, tema, cola, selector con estrella, ajustes y gates del frontend)

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación.
> Cada una queda anotada en [`docs/process/WARNING/`](../../../process/WARNING/README.md) (ficha `005-<tema>.md` con contexto, elegida, descartadas, cómo revertir y cómo comprobarla, y su fila en el README de la carpeta).
> Toda revisión pendiente queda en [`docs/process/PENDING/`](../../../process/PENDING/README.md) (ficha y fila, con qué la cierra).
>
> **Datos del usuario: solo los que crea esta spec**. La spec no borra ni sobrescribe voces grabadas, voces construidas, salidas de `out/` ni modelos descargados que ella no creó. Sus pruebas usan una base en `tmp/spec-005/` y respuestas grabadas. Si algo parece exigir tocar datos existentes, es un `blocked — user-data`.

| Campo | Valor |
| :--- | :--- |
| Tipo | feature |
| Escala | Large (unos 40 archivos nuevos en `client/` y `tests/e2e/`) |
| Rama | `feature/005-client-base` desde `origin/dev`, en `../content-studio-worktrees/005-client-base/` |
| Depende de | [004](../004-server-api/README.md) (fusionada en `origin/dev`) |
| Origen | Pedido del usuario (lote [001-017-studio](../README.md)) |

## Objetivo

Que exista la app de escritorio **Content Studio**: una ventana Tauri 2 que levanta el server de la 004 y muestra la sidebar, el panel de cola (cancelar, reintentar, reordenar y pausar, con progreso en vivo por SSE) y Ajustes (tema claro, oscuro o del sistema, avisos, restablecer elecciones y atajos). También trae el selector reutilizable con estrella y memoria que usan todas las secciones, y los gates del frontend en el test-runner. Las secciones las agrega cada spec siguiente.

## Índice

* [01-contexto-y-decision.md](01-contexto-y-decision.md)
* [02-plan.md](02-plan.md)
* [03-verificacion-final.md](03-verificacion-final.md)

## Fases

| Fase | Qué | Estado |
| :--- | :--- | :--- |
| 1 | Esqueleto: Vite, React, TS, Tailwind v4, shadcn, oxlint, vitest y el catálogo `es.json` | PEN |
| 2 | Tauri: arranque y cierre del server, conexión y plugins | PEN |
| 3 | Shell: sidebar, Ctrl+K, tema, cola con SSE y avisos | PEN |
| 4 | Selector con estrella y Ajustes | PEN |
| 5 | Gates: etapas del client en test-runner, budget, e2e con Playwright y CI | PEN |

## Decisiones clave

* D-1: `client/` con la forma de klinikae (`src/app`, `src/features/<módulo>`, `src/shared`, `src/components/ui`, `messages/es.json` y `tests/unit/src` espejo).
* D-2: Rust delgado. Levanta `studio serve --port 0 --token <t>`, lee la línea `ready` y expone `get_connection()`. El server muere con la ventana (Job Object en Windows).
* D-3: TanStack Query para los datos y SSE para invalidarlos. La navegación es por hash, sin router.
* D-4: tema en `settings` (`ui.theme`), con caché en `localStorage` para pintar sin parpadeo y `setTheme` de la ventana.
* D-5: `<RecommendedSelect>` marca con ★ la opción `recommended`, preselecciona la última elección y la guarda en `settings`.
* D-6: e2e con Playwright contra `vite preview` y la API simulada desde `tests/e2e/_api/`.

## WARNING y PENDING

* WARNING: `005-tanstack-query.md` (dependencia nueva) y `005-ci-windows-rust.md` (`cargo check` en `windows-latest`).
* PENDING: ninguna.

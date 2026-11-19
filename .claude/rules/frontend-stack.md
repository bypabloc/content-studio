---
paths:
  - "client/**"
  - "tests/e2e/**"
---

# Frontend: stack, estructura y comandos (client/)

El client es la ventana de escritorio de Tauri 2. React 19 con TypeScript 5.9 (no 7: `docs/process/WARNING/005-typescript-5.md`), Vite 8, Tailwind 4, TanStack Query para los datos del server y `@dnd-kit` para reordenar la cola. Las versiones fijadas están en la tabla de abajo. Tauri levanta el
server (`studio serve`) en `client/src-tauri/src/server.rs` y el client le habla por HTTP con el token que da `get_connection` (`lib.rs`).

## Comandos (con bun, desde la raíz)

| Qué | Comando |
| :--- | :--- |
| Abrir la app en desarrollo | `bun run --cwd client tauri dev` |
| Solo Vite, sin ventana | `bun run --cwd client dev` |
| Build (mide `client/dist` la etapa `budget`) | `bun run --cwd client build` |
| Tipos, lint y pruebas unitarias | `bun run --cwd client typecheck` · `lint` · `test` |
| Tipos de la API desde OpenAPI | `bun run --cwd client gen:api` (usa `studio openapi`; no se edita `schema.d.ts` a mano) |
| e2e con Playwright y Chromium (una vez: `bun run --cwd tests/e2e playwright install chromium`) | `bun run --cwd tests/e2e test` |
| Compilar el crate de Tauri | `python -m devtools test-runner --type=tauri-check` |

`bun install --frozen-lockfile` en la raíz instala los workspaces `client/` y `tests/e2e/`. `worktree prepare` lo corre en cada worktree (`worktrees.md`).

## Estructura

```
client/
├── src/app/                App, Shell, Sidebar, CommandPalette, native.ts y nav.ts (una línea por sección)
├── src/features/<área>/    una carpeta por sección: queue, settings, ...
├── src/shared/             api (cliente tipado y SSE), i18n (t), theme, hooks, notify, components
├── messages/es.json        todo el texto visible
├── public/theme-init.js    pone la clase dark antes de montar React (la CSP no admite scripts inline)
├── src-tauri/              crate de Tauri: lib.rs (get_connection), server.rs (arranca el server), main.rs
└── tests/unit/src/         espejo de src/ (vitest + Testing Library)
tests/e2e/                  workspace de bun: playwright.config.ts, _api/ (respuestas grabadas), support/, shell|queue|settings
```

## Versiones (fijadas, sin rangos)

Están en `client/package.json`, `tests/e2e/package.json` y `client/src-tauri/Cargo.toml`. Subirlas es un cambio con su spec.

| Pieza | Versión |
| :--- | :--- |
| React y react-dom | 19.3.1 |
| TypeScript | 5.9.3 (no 7: `WARNING/005-typescript-5.md`) |
| Vite · @vitejs/plugin-react | 8.3.8 · 6.3.0 |
| Tailwind (`@tailwindcss/vite`) | 4.3.5 |
| TanStack Query · @dnd-kit/core · @dnd-kit/sortable | 5.108.1 · 6.3.1 · 10.0.0 |
| sonner | 2.0.8 |
| Vitest · Testing Library · jsdom | 5.1.1 · 16.3.3 · 31.0.1 |
| oxlint · openapi-typescript | 1.94.0 · 7.13.0 |
| Playwright · @axe-core/playwright | 1.65.1 · 4.14.0 |
| @tauri-apps/api · plugin-opener (JS) | 2.12.5 · 2.7.3 |
| geist (fuentes) | 1.9.2, declarado sin importar (`WARNING/005-desvios-de-diseno.md`) |
| Tauri (crate) · tauri-build | 2.12.7 · 2.7.6 |
| Plugins de Tauri (crate) | dialog 2.8.4 · opener 2.7.3 · notification 2.8.1 · window-state 2.5.0 |

## Reglas

* **Tamaño**: 300 líneas como máximo por archivo fuente (`.ts`, `.tsx`, `.rs`); las pruebas llegan a 800 (`tests/validators/file-size.json`). Si un archivo se acerca, se divide por responsabilidad.
* **Datos**: el server se pide con `shared/api/client.ts` a través de TanStack Query. Los eventos `job` y `queue` de SSE actualizan la caché (`shared/api/events.ts`) sin volver a pedir. Ningún `fetch` suelto en un componente.
* **Navegación**: por hash (`#/settings`). Las secciones viven en `app/nav.ts`; la barra lateral y la paleta (Ctrl+K) salen de esa lista, así que cada sección nueva agrega su línea ahí.
* **Texto visible**: todo sale de `messages/es.json` con `t('clave')`. Una clave que falta se muestra tal cual, y `catalog-keys.test.ts` falla si sobra o falta una.
* **Cobertura**: 80 % por archivo en `client/src` (sin `main.tsx` ni `components/ui`). Presupuesto del JS inicial: 250 kB gzip (`client/budget.json`).
* **Tema**: `ui.theme` (light, dark o system) vive en `settings`. `useTheme` pone la clase `dark` en `<html>` y `theme-init.js` la pone antes de montar, con la caché de `localStorage`.
* **Pruebas**: un test unitario va en `tests/unit/src/<ruta>/<módulo>.test.ts(x)` (`testing.md`). El e2e usa la API simulada de `tests/e2e/support/app.ts`: no arranca el server real.
* **Ventana**: el menú contextual del navegador queda desactivado; solo sale donde la pantalla pone `data-allow-context` (`app/native.ts`, D-8).

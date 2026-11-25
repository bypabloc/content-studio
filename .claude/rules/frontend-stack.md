---
paths:
  - "client/**"
  - "tests/e2e/**"
---

# Frontend: stack, estructura y comandos (client/)

El client es la ventana de escritorio de Tauri 2. React 19 con TypeScript 5.9 (no 7: `docs/process/WARNING/005-typescript-5.md`), Vite 8, Tailwind 4, TanStack Query para los datos del server y `@dnd-kit` para reordenar la cola. Las versiones fijadas están en la tabla de abajo. 
Tauri se adjunta al server compartido con `studio api up --with-token` (`client/src-tauri/src/server.rs` y `lib.rs`): no lo posee, así que sobrevive a la ventana (spec 028). El client le habla por HTTP con el token que da `get_connection` y, si la red falla, pide la conexión otra vez.

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
| Verificar la app real (CDP, sin Computer Use) | `python -m devtools app-check run` (`verify-before-claiming-done.md` §3) |

`bun install --frozen-lockfile` en la raíz instala los workspaces `client/` y `tests/e2e/`. `worktree prepare` lo corre en cada worktree (`worktrees.md`).

## Estructura

```
client/
├── src/app/                App, Providers, Shell, native.ts y nav.ts (una línea por sección)
├── src/features/<área>/    una carpeta por sección: queue, settings, ...
├── src/shared/             api (cliente tipado y SSE), i18n (t), theme, hooks, notify, forms, components (ui-components.md)
├── (catálogo)              ../server/src/content_studio/messages/{es,en,pt}.json: todo el texto visible (alias @messages)
├── public/theme-init.js    pone la clase dark antes de montar React (la CSP no admite scripts inline)
├── src-tauri/              crate de Tauri: lib.rs (get_connection), server.rs (arranca el server), main.rs
└── tests/unit/src/         espejo de src/ (vitest + Testing Library)
tests/e2e/                  workspace de bun: playwright.config.ts, _api/ (respuestas grabadas), support/, shell|queue|settings
```

## Versiones (fijadas, sin rangos)

Están en `client/package.json`, `tests/e2e/package.json`, `package.json` (raíz) y `client/src-tauri/Cargo.toml`. Subirlas es un cambio con su spec.

Sin `^` ni `~` en los `package.json`: `bun update` solo mueve un rango, así que una versión exacta no cambia sola, y una versión con `^` tampoco es válida aquí. En Cargo.toml, cada versión lleva `=` (`=2.12.7`), y la edición del crate es 2024. `tests/validators/test_pins.py` comprueba la tabla contra los manifiestos (AC-5).

| Paquete | Origen | Versión | Nota |
| :--- | :--- | :--- | :--- |
| `react` | npm | 19.3.1 |  |
| `react-dom` | npm | 19.3.1 |  |
| `typescript` | npm | 5.9.3 | no 7: `WARNING/005-typescript-5.md` |
| `vite` | npm | 8.3.8 |  |
| `@vitejs/plugin-react` | npm | 6.3.0 |  |
| `@tailwindcss/vite` | npm | 4.3.5 |  |
| `@tanstack/react-query` | npm | 5.108.4 |  |
| `@dnd-kit/core` | npm | 6.3.1 |  |
| `@dnd-kit/sortable` | npm | 10.0.0 |  |
| `sonner` | npm | 2.0.8 |  |
| `vitest` | npm | 5.1.1 |  |
| `@testing-library/react` | npm | 16.3.3 |  |
| `jsdom` | npm | 31.0.1 |  |
| `oxlint` | npm | 1.95.0 |  |
| `openapi-typescript` | npm | 7.13.0 |  |
| `@playwright/test` | npm | 1.65.1 |  |
| `@axe-core/playwright` | npm | 4.14.1 |  |
| `@tauri-apps/api` | npm | 2.12.5 |  |
| `@tauri-apps/plugin-opener` | npm | 2.7.3 |  |
| `@tauri-apps/plugin-updater` | npm | 2.14.1 |  |
| `@tauri-apps/plugin-process` | npm | 2.4.0 |  |
| `geist` | npm | 1.9.2 | declarado sin importar (`WARNING/005-desvios-de-diseno.md`) |
| `@base-ui/react` | npm | 1.9.0 | raíz |
| `shadcn` | npm | 4.23.0 | raíz, CLI |
| `tauri` | crate | 2.12.7 |  |
| `tauri-build` | crate | 2.7.6 |  |
| `tauri-plugin-dialog` | crate | 2.8.4 |  |
| `tauri-plugin-opener` | crate | 2.7.3 |  |
| `tauri-plugin-notification` | crate | 2.8.1 |  |
| `tauri-plugin-window-state` | crate | 2.5.0 |  |
| `tauri-plugin-updater` | crate | 2.14.1 |  |
| `tauri-plugin-process` | crate | 2.4.0 |  |

## Instalador y actualizaciones (spec 022)

* El instalador es NSIS por usuario, en español (`bundle.windows.nsis` de `tauri.conf.json`). Sus recursos (`uv.exe`, el server en `app/` y `seed/`) los arma `python -m devtools bundle` y solo los suma `tauri build --config src-tauri/tauri.bundle.json`: `tauri dev` y `cargo check` no los necesitan.
* El updater (`tauri-plugin-updater`) solo se registra en la app instalada; el client lo usa desde `shared/update/useUpdater.ts` (aviso al abrir y Ajustes > Acerca de). Publicar: [release.md](../../docs/operations/release.md).

## Reglas

* **Tamaño**: 300 líneas como máximo por archivo fuente (`.ts`, `.tsx`, `.rs`); las pruebas llegan a 800 (`tests/validators/file-size.json`). Si un archivo se acerca, se divide por responsabilidad.
* **Datos**: el server se pide con `shared/api/client.ts` a través de TanStack Query. Los eventos `job` y `queue` de SSE actualizan la caché (`shared/api/events.ts`) sin volver a pedir. Ningún `fetch` suelto en un componente.
* **Navegación**: por hash (`#/settings`). Las secciones viven en `app/nav.ts`; la barra lateral y la paleta (Ctrl+K) salen de esa lista, así que cada sección nueva agrega su línea ahí.
* **Texto visible**: todo sale del catálogo único (`@messages/{es,en,pt}.json`) con `t('clave')`, en el idioma activo (`shared/i18n/locale.ts`, con respaldo a español). Una clave que falta se muestra tal cual; la etapa `i18n` falla si una clave falta en un idioma, sobra o no tiene texto (spec 007, D-8).
* **Cobertura**: 80 % por archivo en `client/src` (sin `main.tsx`, `shared/components/shadcn/` ni los `.d.ts`). Presupuesto del JS inicial: 232 kB gzip (`client/budget.json`).
* **Tema**: `ui.theme` (light, dark o system) vive en `settings`. `useTheme` pone la clase `dark` en `<html>` y `theme-init.js` la pone antes de montar, con la caché de `localStorage`.
* **Pruebas**: un test unitario va en `tests/unit/src/<ruta>/<módulo>.test.ts(x)` (`testing.md`). El e2e usa la API simulada de `tests/e2e/support/app.ts`: no arranca el server real.
* **Componentes**: las pantallas arman su layout con átomos, moléculas y organismos, nunca con etiquetas nativas; la jerarquía y los textos están en `ui-components.md`.
* **Ventana**: el menú contextual del navegador queda desactivado; solo sale donde la pantalla pone `data-allow-context` (`app/native.ts`, D-8).

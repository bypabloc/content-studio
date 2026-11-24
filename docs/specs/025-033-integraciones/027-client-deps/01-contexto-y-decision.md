# Spec 027: contexto y decisión

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación.
> Cada una queda anotada en [`docs/process/WARNING/`](../../../process/WARNING/README.md) (ficha `027-<tema>.md` con contexto, elegida, descartadas, cómo revertir y cómo comprobarla, y su fila en el README de la carpeta).
> Toda revisión pendiente queda en [`docs/process/PENDING/`](../../../process/PENDING/README.md) (ficha y fila, con qué la cierra).
>
> **Datos del usuario: solo los que crea esta spec**. La spec no borra ni sobrescribe voces grabadas (`server/data/narration/voz/`), voces construidas, salidas de `out/` ni modelos descargados que ella no creó. Sus pruebas escriben en carpetas nuevas (`out/<herramienta>/spec-027/` o `tmp/spec-027/`). Si algo parece exigir tocar datos existentes, no se decide al ejecutar: es un `blocked — user-data` y se pregunta. Los cambios locales o sin rastrear del checkout principal no son de la spec: no se tocan y no bloquean.

## 1. Precondición

```bash
git fetch origin dev
git log origin/dev --merges --oneline | grep -q 'chore/025-server-python' || echo FALLA
bun --version && cargo --version && rustc --version
```

## 2. Contexto

El client fija versiones exactas: React 19.3.1, TypeScript 5.9.3, Vite 8.3.8, Tailwind 4.3.5, TanStack Query 5.108.1, Vitest 5.1.1, Playwright 1.65.1, Tauri 2.12.7 y sus plugins (`client/package.json`, `client/src-tauri/Cargo.toml`). La tabla de `frontend-stack.md` repite esas versiones a mano. El crate usa la edición de Rust 2021.

### Términos

| Término | Significado | En el código |
| :--- | :--- | :--- |
| Manifiestos | `client/package.json`, `tests/e2e/package.json`, `package.json` y `client/src-tauri/Cargo.toml` | — |
| Tabla de versiones | La sección «Versiones» de `.agents/rules/frontend-stack.md` | D-4 |

### Hallazgos de la exploración

- **Versiones exactas en los manifiestos** (2026-11-24): `client/package.json` y `Cargo.toml` (`=2.12.7`, `=2.8.4`…).
- **TypeScript 5 por openapi-typescript**: `docs/process/WARNING/005-typescript-5.md`.
- **`edition = "2021"`** en `client/src-tauri/Cargo.toml`.
- **`windows = "=0.62.2"`** con las features de Job Objects que usa `server::job` (`client/src-tauri/src/server.rs`).
- **Presupuesto**: 232 kB gzip del JS inicial (`client/budget.json`).

## 3. Solución

- `bun update --latest` por workspace y versiones exactas; adaptar lo que rompa (D-1, D-2).
- `cargo update` y versiones exactas en `Cargo.toml`; edición 2024 (D-3).
- Test que compara la tabla de la regla con los manifiestos (D-4) y la tabla actualizada.

Cada decisión pasa por la escalera de plan-format.md §0 (¿debe existir? ¿ya existe? ¿stdlib o una dependencia que ya está?).

- **D-1: Última versión estable, exacta** — Es software nuevo y el usuario pidió lo más actual; las versiones exactas ya son la regla (`frontend-stack.md`). Se descarta rangos `^`, porque la regla los prohíbe y rompen la reproducibilidad del instalador.
- **D-2: TypeScript condicionado a openapi-typescript** — `gen:api` usa la API JavaScript de TypeScript, que TS 7 (nativo en Go) no expone (`WARNING/005-typescript-5.md`). Se descarta dos compiladores, descartado en la 005.
- **D-3: Edición 2024** — `edition = "2021"` en `client/src-tauri/Cargo.toml`; la 2024 es la actual. Se descarta quedarse en 2021, porque contradice «lo más actual».
- **D-4: Tabla de versiones comprobada** — La tabla se escribe a mano y se desfasa en cada actualización. Se descarta generar la tabla, porque agrega un paso al flujo para algo que un test resuelve.

## 4. Fuera de alcance

- Cambiar de librería (por ejemplo, otro gestor de estado o de UI).
- Python (025) y motores (026).
- Rediseño visual: lo que cambie la apariencia por una versión nueva se corrige para que se vea igual.

## 5. Criterios de aceptación

- **AC-1**: WHEN se leen los manifiestos THEN cada dependencia es exacta y es la última estable del día del merge (`bun outdated` en cada workspace y el registro de crates.io sin versiones nuevas para las directas).
- **AC-2**: WHEN se corre `bun run --cwd client gen:api` y `typecheck` THEN pasan con la versión de TypeScript que permite D-2.
- **AC-3**: WHEN se corre `python -m devtools test-runner --type=all`, `--type=e2e` y `--type=tauri-check` THEN pasan y el JS inicial queda en 232 kB gzip o menos.
- **AC-4**: WHEN `python -m devtools app-check run` recorre el smoke en claro y oscuro THEN pasa, sin errores en la consola.
- **AC-5**: WHEN una versión de la tabla de `frontend-stack.md` difiere de su manifiesto THEN un test falla nombrando el paquete.

## 6. Debe sonar / no debe sonar

No aplica: la spec no cambia cómo se genera el audio.

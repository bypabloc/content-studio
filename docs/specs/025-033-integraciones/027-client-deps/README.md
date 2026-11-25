# Spec 027: Client y Tauri con todas sus dependencias en la última versión

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación.
> Cada una queda anotada en [`docs/process/WARNING/`](../../../process/WARNING/README.md) (ficha `027-<tema>.md` con contexto, elegida, descartadas, cómo revertir y cómo comprobarla, y su fila en el README de la carpeta).
> Toda revisión pendiente queda en [`docs/process/PENDING/`](../../../process/PENDING/README.md) (ficha y fila, con qué la cierra).
>
> **Datos del usuario: solo los que crea esta spec**. La spec no borra ni sobrescribe voces grabadas (`server/data/narration/voz/`), voces construidas, salidas de `out/` ni modelos descargados que ella no creó. Sus pruebas escriben en carpetas nuevas (`out/<herramienta>/spec-027/` o `tmp/spec-027/`). Si algo parece exigir tocar datos existentes, no se decide al ejecutar: es un `blocked — user-data` y se pregunta. Los cambios locales o sin rastrear del checkout principal no son de la spec: no se tocan y no bloquean.

| Campo | Valor |
| :--- | :--- |
| Tipo | chore |
| Escala | Medium (6–10 archivos) |
| Rama | `chore/027-client-deps` desde `origin/dev`, en `../content-studio-worktrees/027-client-deps/` |
| Depende de | 025 (lock y CI de Python ya al día; esta spec no toca Python) |
| Origen | Pedido del usuario (2026-11-24) · [`docs/research/integraciones-locales/`](../../../research/integraciones-locales/README.md) |

## Objetivo

Las dependencias de JavaScript (client y e2e), del crate de Tauri y de Rust pasan a su última versión estable, fijadas exactas, y la tabla de versiones de las reglas no puede quedar desfasada.

## Cuándo leer cada archivo

| Archivo | Qué trae | Cuándo leer |
| :--- | :--- | :--- |
| [01-contexto-y-decision.md](01-contexto-y-decision.md) | Precondición, términos, hallazgos, decisiones D-n, fuera de alcance, AC | Primero |
| [fases/1-javascript/](fases/1-javascript/plan-tdd.md) | Ciclos TDD, archivos y commit de la fase 1 | Al implementar la fase 1 |
| [fases/2-rust/](fases/2-rust/plan-tdd.md) | Ciclos TDD, archivos y commit de la fase 2 | Al implementar la fase 2 |
| [fases/3-tabla/](fases/3-tabla/plan-tdd.md) | Ciclos TDD, archivos y commit de la fase 3 | Al implementar la fase 3 |
| [03-verificacion-final.md](03-verificacion-final.md) | Batería, comprobaciones, cierre y PR | Con todos los commits hechos |

## Estado por fase

Estados: `PEN` (pendiente) o `IMP` (implementada, con su commit). El estado va en la última columna.

| Fase | Qué | Ciclos | AC | Commit | Estado |
| :--- | :--- | :--- | :--- | :--- | :--- |
| F1 | [Dependencias de JavaScript](fases/1-javascript/plan-tdd.md) | C1 | AC-1, AC-2, AC-3 | pendiente | IMP |
| F2 | [Tauri y Rust](fases/2-rust/plan-tdd.md) | C2 | AC-1, AC-3, AC-4 | pendiente | IMP |
| F3 | [Tabla de versiones comprobada](fases/3-tabla/plan-tdd.md) | C3 | AC-5 | pendiente | IMP |
| FV | [Verificación final](03-verificacion-final.md) | - | todos | - | IMP |

## Decisiones cerradas (no reabrir)

Una línea por decisión; el motivo y la alternativa descartada van en [01 §3](01-contexto-y-decision.md#3-solución).

1. **D-1**: Todas las dependencias de `client/package.json`, `tests/e2e/package.json`, `package.json` (raíz) y `client/src-tauri/Cargo.toml` a la última estable, exactas (usuario, 2026-11-24).
2. **D-2**: TypeScript sube a 7 solo si `openapi-typescript` lo declara en su `peerDependencies`; si no, la última 5.x y se actualiza `WARNING/005-typescript-5.md` (agente, 2026-11-24).
3. **D-3**: El crate de Tauri pasa a la edición de Rust 2024 si la versión estable de Rust la soporta, con `cargo fix --edition` (agente, 2026-11-24).
4. **D-4**: Un test compara la tabla «Versiones» de `frontend-stack.md` con los manifiestos (agente, 2026-11-24).

## Reglas críticas

- Versiones exactas, sin `^` ni `~` (`frontend-stack.md`).
- Un cambio de API de una librería se adapta en el código, sin fijar la versión vieja sin su ficha WARNING.
- El presupuesto del JS inicial (232 kB gzip, `client/budget.json`) no sube; si una versión nueva lo supera, se registra y se busca la causa.
- Componentes: la jerarquía de `ui-components.md` no cambia; `shadcn/` se regenera con su CLI, no a mano.
- Cada archivo fuente en 300 líneas o menos.

## Matriz de verificación

Todo AC tiene al menos un test. Se completa al redactar y se marca al implementar.

| AC | Fase | Ciclo | Test | Verificación real |
| :--- | :--- | :--- | :--- | :--- |
| AC-1 | F1 | C1 | `tests/validators/test_pins.py::test_ac1_versiones_exactas` | solo pytest |
| AC-1 | F2 | C2 | `cargo test --manifest-path client/src-tauri/Cargo.toml` | solo pytest |
| AC-2 | F1 | C1 | `bun run --cwd client gen:api && bun run --cwd client typecheck` | solo pytest |
| AC-3 | F1 | C1 | `python -m devtools test-runner --type=all` | solo pytest |
| AC-3 | F2 | C2 | `cargo test --manifest-path client/src-tauri/Cargo.toml` | solo pytest |
| AC-4 | F2 | C2 | `python -m devtools app-check run` | smoke en claro y oscuro |
| AC-5 | F3 | C3 | `tests/validators/test_pins.py::test_ac5_tabla_de_la_regla_coincide` | solo pytest |

## WARNING y PENDING

- WARNING: `005-typescript-5` se actualiza o se borra (D-2); `027-edicion-2024` (D-3).
- PENDING: las librerías que no se pudieron subir, una ficha cada una.

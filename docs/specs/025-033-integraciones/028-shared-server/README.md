# Spec 028: Server compartido: arranque bajo demanda, descubrimiento, token persistente y apagado por inactividad

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación.
> Cada una queda anotada en [`docs/process/WARNING/`](../../../process/WARNING/README.md) (ficha `028-<tema>.md` con contexto, elegida, descartadas, cómo revertir y cómo comprobarla, y su fila en el README de la carpeta).
> Toda revisión pendiente queda en [`docs/process/PENDING/`](../../../process/PENDING/README.md) (ficha y fila, con qué la cierra).
>
> **Datos del usuario: solo los que crea esta spec**. La spec no borra ni sobrescribe voces grabadas (`server/data/narration/voz/`), voces construidas, salidas de `out/` ni modelos descargados que ella no creó. Sus pruebas escriben en carpetas nuevas (`out/<herramienta>/spec-028/` o `tmp/spec-028/`). Si algo parece exigir tocar datos existentes, no se decide al ejecutar: es un `blocked — user-data` y se pregunta. Los cambios locales o sin rastrear del checkout principal no son de la spec: no se tocan y no bloquean.

| Campo | Valor |
| :--- | :--- |
| Tipo | feature |
| Escala | Large (11+ archivos) |
| Rama | `feature/028-shared-server` desde `origin/dev`, en `../content-studio-worktrees/028-shared-server/` |
| Depende de | 027 (manifiestos del client al día) |
| Origen | Pedido del usuario (2026-11-24) · [`docs/research/integraciones-locales/`](../../../research/integraciones-locales/README.md) |

## Objetivo

Cualquier app de la PC encuentra y usa el mismo server local: arranca solo cuando alguien lo pide (la ventana, el MCP o un script), deja su dirección en un archivo conocido con un token que no cambia, y se apaga tras un rato sin uso aunque la ventana esté abierta.

## Cuándo leer cada archivo

| Archivo | Qué trae | Cuándo leer |
| :--- | :--- | :--- |
| [01-contexto-y-decision.md](01-contexto-y-decision.md) | Precondición, términos, hallazgos, decisiones D-n, fuera de alcance, AC | Primero |
| [02-diseno.md](02-diseno.md) | Flujo, CLI `studio api`, archivos de descubrimiento, módulos y textos | Antes de la primera fase |
| [fases/1-runtime/](fases/1-runtime/plan-tdd.md) | Ciclos TDD, archivos y commit de la fase 1 | Al implementar la fase 1 |
| [fases/2-tauri/](fases/2-tauri/plan-tdd.md) | Ciclos TDD, archivos y commit de la fase 2 | Al implementar la fase 2 |
| [fases/3-client/](fases/3-client/plan-tdd.md) | Ciclos TDD, archivos y commit de la fase 3 | Al implementar la fase 3 |
| [03-verificacion-final.md](03-verificacion-final.md) | Batería, comprobaciones, cierre y PR | Con todos los commits hechos |

## Estado por fase

Estados: `PEN` (pendiente) o `IMP` (implementada, con su commit). El estado va en la última columna.

| Fase | Qué | Ciclos | AC | Commit | Estado |
| :--- | :--- | :--- | :--- | :--- | :--- |
| F1 | [Runtime del server](fases/1-runtime/plan-tdd.md) | C1, C2, C3, C4 | AC-4, AC-1, AC-2, AC-3, AC-6, AC-5, AC-10 | pendiente | IMP |
| F2 | [La ventana se adjunta](fases/2-tauri/plan-tdd.md) | C5 | AC-7, AC-9 | pendiente | IMP |
| F3 | [Reconexión y Ajustes > Integraciones](fases/3-client/plan-tdd.md) | C6, C7 | AC-8, AC-11 | pendiente | IMP |
| FV | [Verificación final](03-verificacion-final.md) | - | todos | - | PEN |

## Decisiones cerradas (no reabrir)

Una línea por decisión; el motivo y la alternativa descartada van en [01 §3](01-contexto-y-decision.md#3-solución).

1. **D-1**: Puerto por defecto 41830 (IANA sin asignar, fuera del rango dinámico), configurable en `api.port`; si está ocupado o reservado, el que elige el sistema, anotado en `api.json` (usuario y agente, 2026-11-24).
2. **D-2**: Descubrimiento en `api.json` y token en `api-token`, junto a la base (`paths.db_path().parent`) (agente, 2026-11-24).
3. **D-3**: Token persistente por instalación; `studio api token --rotate` lo cambia (agente, 2026-11-24).
4. **D-4**: Una sola instancia por instalación con un lock de archivo retenido por el server (agente, 2026-11-24).
5. **D-5**: Se apaga tras `api.idle_minutes` (10) sin peticiones (salvo `/health` y `/events`) y sin trabajos en cola ni corriendo, también con la ventana abierta; la próxima llamada lo reactiva (usuario, 2026-11-24).
6. **D-6**: El server ya no vive en el Job de la ventana: sobrevive a su cierre; el updater lo detiene antes de instalar (agente, 2026-11-24).
7. **D-7**: `TrustedHostMiddleware` con `127.0.0.1` y `localhost` (agente, 2026-11-24).

## Reglas críticas

- Solo lo que piden los AC; nada de «Fuera de alcance».
- `runtime/` y `cli/` solo importan stdlib (dos capas); la API sigue en `api/`.
- El token nunca se imprime en logs ni en la salida de `status`; `--with-token` existe solo para Tauri.
- Bind siempre a `127.0.0.1` (la LAN es la 032).
- Textos visibles en los tres catálogos; mensajes del CLI en inglés.
- Cada `.py` de fuente en 300 líneas o menos; tests en 800.

## Matriz de verificación

Todo AC tiene al menos un test. Se completa al redactar y se marca al implementar.

| AC | Fase | Ciclo | Test | Verificación real |
| :--- | :--- | :--- | :--- | :--- |
| AC-1 | F1 | C2 | `server/tests/integration/test_shared_server.py::test_ac1_up_starts_and_writes_api_json` | 03 §2, paso 1 |
| AC-2 | F1 | C2 | `server/tests/integration/test_shared_server.py::test_ac2_two_up_one_server` | 03 §2, paso 1 |
| AC-3 | F1 | C2 | `server/tests/integration/test_shared_server.py::test_ac3_busy_port_uses_another` | 03 §2, paso 1 |
| AC-4 | F1 | C1 | `server/tests/unit/src/content_studio/runtime/test_discovery.py::test_ac4_token_persists_and_rotates` | solo pytest |
| AC-5 | F1 | C3 | `server/tests/unit/src/content_studio/runtime/test_idle.py::test_ac5_exits_when_idle_but_not_with_jobs` | solo pytest |
| AC-6 | F1 | C2 | `server/tests/unit/src/content_studio/cli/test_api.py::test_ac6_down_respects_running_job` | 03 §2, paso 1 |
| AC-7 | F2 | C5 | `client/src-tauri/src/lib.rs::tests::connect_attaches_to_running_server` | 03 §2, paso 2 |
| AC-8 | F3 | C6 | `client/tests/unit/src/shared/api/client.test.ts` | e2e `happy-server-wakes` |
| AC-9 | F2 | C5 | `client/src-tauri/src/lib.rs::tests::restarts_server_of_other_version` | 03 §2, paso 3 |
| AC-10 | F1 | C4 | `server/tests/unit/src/content_studio/api/test_guards.py::test_ac10_foreign_host_gets_400` | solo pytest |
| AC-11 | F3 | C7 | `client/tests/unit/src/features/settings/IntegrationsPanel.test.tsx` | e2e `happy-integrations` |

## WARNING y PENDING

- WARNING: `028-puerto-41830` (D-1), `028-server-fuera-del-job` (D-6).
- PENDING: ninguna prevista.

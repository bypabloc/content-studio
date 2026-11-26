# Spec 032: Red local: emparejar dispositivos, tokens con permisos, subir archivos y MCP por HTTP

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación.
> Cada una queda anotada en [`docs/process/WARNING/`](../../../process/WARNING/README.md) (ficha `032-<tema>.md` con contexto, elegida, descartadas, cómo revertir y cómo comprobarla, y su fila en el README de la carpeta).
> Toda revisión pendiente queda en [`docs/process/PENDING/`](../../../process/PENDING/README.md) (ficha y fila, con qué la cierra).
>
> **Datos del usuario: solo los que crea esta spec**. La spec no borra ni sobrescribe voces grabadas (`server/data/narration/voz/`), voces construidas, salidas de `out/` ni modelos descargados que ella no creó. Sus pruebas escriben en carpetas nuevas (`out/<herramienta>/spec-032/` o `tmp/spec-032/`). Si algo parece exigir tocar datos existentes, no se decide al ejecutar: es un `blocked — user-data` y se pregunta. Los cambios locales o sin rastrear del checkout principal no son de la spec: no se tocan y no bloquean.

| Campo | Valor |
| :--- | :--- |
| Tipo | feature |
| Escala | Large (11+ archivos) |
| Rama | `feature/032-lan` desde `origin/dev`, en `../content-studio-worktrees/032-lan/` |
| Depende de | 031 (cierra la integración local; usa 028, 029 y 030) |
| Origen | Pedido del usuario (2026-11-24) · [`docs/research/integraciones-locales/`](../../../research/integraciones-locales/README.md) |

## Objetivo

Un celular u otra PC de la misma red puede emparejarse con un PIN, subir archivos, pedir trabajos (también por MCP) y descargar sus resultados, sin acceso a los archivos ni a la administración de esta PC. Está apagado hasta que el usuario lo activa.

## Cuándo leer cada archivo

| Archivo | Qué trae | Cuándo leer |
| :--- | :--- | :--- |
| [01-contexto-y-decision.md](01-contexto-y-decision.md) | Precondición, términos, hallazgos, decisiones D-n, fuera de alcance, AC | Primero |
| [02-diseno.md](02-diseno.md) | Flujo, rutas de la LAN, tablas, módulos, firewall y textos | Antes de la primera fase |
| [fases/1-acceso/](fases/1-acceso/plan-tdd.md) | Ciclos TDD, archivos y commit de la fase 1 | Al implementar la fase 1 |
| [fases/2-superficie/](fases/2-superficie/plan-tdd.md) | Ciclos TDD, archivos y commit de la fase 2 | Al implementar la fase 2 |
| [fases/3-firewall-y-ui/](fases/3-firewall-y-ui/plan-tdd.md) | Ciclos TDD, archivos y commit de la fase 3 | Al implementar la fase 3 |
| [03-verificacion-final.md](03-verificacion-final.md) | Batería, comprobaciones, cierre y PR | Con todos los commits hechos |

## Estado por fase

Estados: `PEN` (pendiente) o `IMP` (implementada, con su commit). El estado va en la última columna.

| Fase | Qué | Ciclos | AC | Commit | Estado |
| :--- | :--- | :--- | :--- | :--- | :--- |
| F1 | [Listener, dispositivos y emparejamiento](fases/1-acceso/plan-tdd.md) | C1, C2, C3 | AC-1, AC-2, AC-11, AC-4, AC-7, AC-3 | fase 1 | IMP |
| F2 | [Rutas remotas, subidas y MCP por HTTP](fases/2-superficie/plan-tdd.md) | C4, C5, C6 | AC-5, AC-6, AC-8 | - | PEN |
| F3 | [Firewall y Ajustes](fases/3-firewall-y-ui/plan-tdd.md) | C7, C8 | AC-9, AC-10 | - | PEN |
| FV | [Verificación final](03-verificacion-final.md) | - | todos | - | PEN |

## Decisiones cerradas (no reabrir)

Una línea por decisión; el motivo y la alternativa descartada van en [01 §3](01-contexto-y-decision.md#3-solución).

1. **D-1**: Apagado por defecto; al activarlo, un segundo listener en la IP elegida y el puerto 41831, con TLS; el de 127.0.0.1 no cambia (agente, 2026-11-24).
2. **D-2**: Desde la LAN solo se suben archivos y se descargan salidas propias; nunca rutas de esta PC (usuario, 2026-11-24).
3. **D-3**: Emparejamiento con PIN de 6 dígitos (5 min, un uso, 5 intentos) y un token por dispositivo con permisos `jobs` y `files`, guardado como hash y revocable (agente, 2026-11-24).
4. **D-4**: TLS con certificado autofirmado y huella SHA-256 fijada al emparejar; dependencia `cryptography` (agente, 2026-11-24).
5. **D-5**: Regla de firewall solo para el perfil Privado, creada con `netsh` elevado (UAC) al activar y borrada al desactivar (agente, 2026-11-24).
6. **D-6**: MCP por Streamable HTTP en `/mcp` del listener de la LAN, con el token del dispositivo y `Origin` validado (agente, 2026-11-24).
7. **D-7**: Sin mDNS: la app muestra la URL; el acceso fuera de casa se documenta con Tailscale Serve (agente, 2026-11-24).

## Reglas críticas

- Apagado por defecto: ningún test ni arranque abre un socket fuera de 127.0.0.1 si `api.lan.enabled` es falso.
- Las rutas de la LAN son una lista cerrada (02 §2); una ruta nueva en la API no aparece en la LAN sin agregarla ahí y a su test.
- Los tokens se guardan como sha256; el token en claro solo se devuelve una vez, al emparejar.
- `lan/` importa `cryptography` y el SDK dentro de funciones.
- Textos visibles en los tres catálogos; mensajes del CLI en inglés.
- Cada `.py` de fuente en 300 líneas o menos; tests en 800.

## Matriz de verificación

Todo AC tiene al menos un test. Se completa al redactar y se marca al implementar.

| AC | Fase | Ciclo | Test | Verificación real |
| :--- | :--- | :--- | :--- | :--- |
| AC-1 | F1 | C1 | `server/tests/integration/test_lan.py::test_ac1_off_only_loopback` | solo pytest |
| AC-2 | F1 | C1 | `server/tests/integration/test_lan.py::test_ac2_tls_listener_with_fingerprint` | solo pytest |
| AC-3 | F1 | C3 | `server/tests/unit/src/content_studio/lan/test_pairing.py::test_ac3_pin_single_use_expires_and_locks` | solo pytest |
| AC-4 | F1 | C2 | `server/tests/unit/src/content_studio/lan/test_clients.py::test_ac4_no_revoked_or_local_token_is_401` | solo pytest |
| AC-5 | F2 | C4 | `server/tests/unit/src/content_studio/api/test_app.py::test_ac5_remote_without_admin_routes` | solo pytest |
| AC-6 | F2 | C5 | `server/tests/unit/src/content_studio/lan/test_guard.py::test_ac6_upload_yes_path_no` | solo pytest |
| AC-7 | F1 | C2 | `server/tests/integration/test_lan.py::test_ac7_only_own_jobs` | solo pytest |
| AC-8 | F2 | C6 | `server/tests/integration/test_lan.py::test_ac8_mcp_http_lists_and_checks_origin` | 03 §2, paso 3 |
| AC-9 | F3 | C7 | `client/src-tauri/src/firewall.rs::tests::builds_private_profile_rule` | 03 §2, paso 1 |
| AC-10 | F3 | C8 | `client/tests/unit/src/features/settings/LanPanel.test.tsx` | e2e `happy-lan-pairing` |
| AC-11 | F1 | C1 | `server/tests/integration/test_lan.py::test_ac11_keep_awake` | solo pytest |

## WARNING y PENDING

- WARNING: `032-lan-opt-in` (D-1), `032-cryptography` (dependencia nueva), `032-firewall-uac` (D-5).
- PENDING: `032-prueba-con-celular` si no se pudo probar desde un dispositivo real; `032-mdns` en `03-later/` si el usuario lo pide.

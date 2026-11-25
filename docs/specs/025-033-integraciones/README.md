# Lote 025–033: integraciones locales

Pedido del usuario (2026-11-24): que las apps de la PC, los LLM y agentes locales y los equipos de la red local puedan pedirle trabajos a content-studio y recibir el archivo, con el server arrancando bajo demanda. Antes, todo el proyecto pasa a la Python más alta disponible y a las últimas versiones de sus dependencias. Investigación: [`docs/research/integraciones-locales/`](../../research/integraciones-locales/README.md).

Formato: [`plan-format.md`](../../../.agents/rules/plan-format.md). Cada spec es una rama desde `origin/dev` y un PR a `dev`, en orden. La 033 hace la verificación integral y borra esta carpeta.

## Specs

| Spec | Qué | Tipo | Escala | Depende de | Estado |
| :--- | :--- | :--- | :--- | :--- | :--- |
| [025](025-server-python/README.md) | Server, devtools, CI e instalador en la Python más alta (3.15) con las dependencias al día | chore | Medium | 023 | DON |
| [026](026-engines-python/README.md) | Venvs de los motores en la Python, torch y librerías más altas que soporte cada uno | chore | Large | 025 | DON |
| [027](027-client-deps/README.md) | Client y Tauri con todas sus dependencias en la última versión | chore | Medium | 025 | PEN |
| [028](028-shared-server/README.md) | Server compartido: arranque bajo demanda, descubrimiento, token persistente y apagado por inactividad | feature | Large | 027 | PEN |
| [029](029-mcp/README.md) | Servidor MCP local (`studio mcp`) para LLMs y agentes | feature | Large | 028 | PEN |
| [030](030-hot-folders/README.md) | Carpetas de entrada: soltar un archivo y recibir el resultado | feature | Large | 029 | PEN |
| [031](031-windows-integration/README.md) | Windows: enlaces `content-studio://`, «Enviar a» e inicio con Windows | feature | Medium | 030 | PEN |
| [032](032-lan/README.md) | Red local: emparejar dispositivos, tokens con permisos, subir archivos y MCP por HTTP | feature | Large | 031 | PEN |
| [033](033-integral-verification/README.md) | Verificación integral y cierre del lote | chore | Micro | 032 | PEN |

## Decisiones del usuario que valen para todo el lote

* **Versiones**: la Python estable más alta (3.15 hoy); si una pieza no la soporta, la anterior, y así. Todas las librerías y paquetes en su última versión: server, devtools, client, Tauri y los venvs de cada motor (cada uno en la Python más alta que soporte). La actualización va antes de las integraciones, partida en tres specs (025 server, 026 motores, 027 client) porque la plantilla divide lo que pasa de 8 ciclos.
* **Puerto**: fijo y configurable; el agente eligió 41830 (sin asignar en IANA y fuera de las exclusiones de este equipo), con respaldo si está ocupado. La red local usa 41831.
* **Inactividad**: el server se apaga sin uso aunque la ventana esté abierta, y lo reactiva la próxima llamada (de la ventana o del MCP). Las carpetas de entrada y la red local pueden pedir mantenerlo encendido.
* **Herramientas MCP**: las decide el agente según la investigación: pocas por tarea más una genérica.
* **Entradas**: desde esta PC, cualquier ruta del sistema; desde la red local, solo archivos subidos.
* **Carpetas de entrada**: donde las indique el cliente.

## Orden y dependencias

```text
023 (cierra el lote 001–023) → 025 → 026 → 027 → 028 → 029 → 030 → 031 → 032 → 033
```

Se ejecutan con `run-specs` en orden numérico. La 026 usa la GPU por motor (`turno-gpu.md`) y es la más larga.

# Spec 032: contexto y decisión

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación.
> Cada una queda anotada en [`docs/process/WARNING/`](../../../process/WARNING/README.md) (ficha `032-<tema>.md` con contexto, elegida, descartadas, cómo revertir y cómo comprobarla, y su fila en el README de la carpeta).
> Toda revisión pendiente queda en [`docs/process/PENDING/`](../../../process/PENDING/README.md) (ficha y fila, con qué la cierra).
>
> **Datos del usuario: solo los que crea esta spec**. La spec no borra ni sobrescribe voces grabadas (`server/data/narration/voz/`), voces construidas, salidas de `out/` ni modelos descargados que ella no creó. Sus pruebas escriben en carpetas nuevas (`out/<herramienta>/spec-032/` o `tmp/spec-032/`). Si algo parece exigir tocar datos existentes, no se decide al ejecutar: es un `blocked — user-data` y se pregunta. Los cambios locales o sin rastrear del checkout principal no son de la spec: no se tocan y no bloquean.

## 1. Precondición

```bash
git fetch origin dev
git log origin/dev --merges --oneline | grep -q 'feature/031-windows-integration' || echo FALLA
git cat-file -e origin/dev:server/src/content_studio/inbox/inputs.py || echo FALLA
git cat-file -e origin/dev:server/src/content_studio/mcp_server/bridge.py || echo FALLA
```

## 2. Contexto

Con las specs 028 a 031, todo lo que corre en esta PC puede pedir trabajos. Otro equipo de la casa no puede: el server escucha solo en 127.0.0.1, el token es uno solo (y abre también la administración) y las entradas son rutas de esta PC, que un celular no tiene.

### Términos

| Término | Significado | En el código |
| :--- | :--- | :--- |
| Listener de la LAN | El segundo `uvicorn.Server`, en la IP de la red y con TLS | `lan/server.py` |
| Dispositivo | Un cliente emparejado con su token y sus permisos | tabla `api_clients` |
| Subida | Un archivo que un dispositivo sube para usarlo como entrada | tabla `uploads`, `upload:<id>` |
| Huella | SHA-256 del certificado autofirmado | `lan/cert.py` |

### Hallazgos de la exploración

- **Bind fijo a 127.0.0.1**: `uvicorn.Config(app, host='127.0.0.1', …)` en `cli/serve.py`.
- **Un solo token** compara con `secrets.compare_digest` en `_token_guard` (`api/app.py`).
- **Rutas administrativas**: `engines`, `storage`, `settings`, `fs`, `library_actions`, `system` (`create_app`, `api/app.py`).
- **Guarda de archivos**: `allowed_file` (`api/paths_guard.py`) limita `/files` a `out/` y referencias.
- **Entradas por operación**: `INPUT_PARAM` de `inbox/inputs.py` (030).
- **Exclusiones de puertos de este equipo** (2026-11-24): 41831 queda fuera.

## 3. Solución

- Paquete `lan/`: dispositivos, PIN, certificado, guarda de parámetros y el listener.
- `create_app(..., remote=True)` con la lista cerrada de rutas, subidas y MCP por HTTP.
- Regla de firewall con UAC desde Tauri.
- Ajustes > Integraciones > Red local.
- `docs/operations/lan.md` con cómo emparejar, la huella y Tailscale Serve para fuera de casa.

Cada decisión pasa por la escalera de plan-format.md §0 (¿debe existir? ¿ya existe? ¿stdlib o una dependencia que ya está?).

- **D-1: Listener aparte y opt-in** — Ollama abre `0.0.0.0` sin autenticación (investigación §6): el contraejemplo. Separar listeners deja la superficie de la LAN en una app propia, sin tocar la local. Se descarta abrir el mismo listener a `0.0.0.0`, porque mezcla clientes de confianza y remotos en las mismas rutas.
- **D-2: Entradas remotas por subida** — El usuario lo eligió: «Local: todo; LAN: subir». Se descarta rutas del sistema también desde la LAN, que el usuario descartó.
- **D-3: PIN y tokens por dispositivo** — Es el modelo de LocalSend y de OBS: el usuario ve el PIN en la pantalla de la PC y puede revocar un celular perdido sin rotar el token local. Se descarta compartir el token local, porque no se puede revocar por dispositivo y abre la administración.
- **D-4: TLS autofirmado** — Sin TLS el token viaja en claro por el Wi-Fi. La stdlib no genera certificados; `cryptography` es la librería estándar de facto. LocalSend y KDE Connect usan huella con confianza al primer uso. Se descarta HTTP en claro, y `mkcert`, que exige instalar una CA en cada dispositivo.
- **D-5: Firewall con UAC** — El instalador es por usuario y sin admin; crear una regla de entrada pide elevación. Limitarla al perfil Privado evita exponer el puerto en redes públicas. Se descarta dejar que Windows muestre su aviso al escuchar, porque su comportamiento sin admin no está verificado (investigación §6).
- **D-6: MCP remoto** — Open WebUI solo habla Streamable HTTP y los clientes de otra PC no pueden lanzar `studio mcp`. La spec exige validar `Origin` y autenticar (investigación §3). Se descarta un proxy aparte, que agrega un proceso.
- **D-7: Sin descubrimiento automático** — El emparejamiento ya exige mirar la pantalla de la PC (el PIN), así que copiar la URL no suma pasos. Un túnel público está fuera del pedido. Se descarta `zeroconf`, una dependencia más para ahorrar copiar una URL.

## 4. Fuera de alcance

- Acceso desde internet, túneles públicos y Tailscale integrado (solo documentado, D-7).
- mDNS (D-7).
- Una app para celular: el dispositivo usa la API, un navegador con un cliente propio o un cliente MCP.
- Varios usuarios con permisos distintos en la misma PC.

## 5. Criterios de aceptación

- **AC-1**: Given `api.lan.enabled` falso When arranca el server Then solo hay sockets en 127.0.0.1.
- **AC-2**: WHEN se activa la red local con una IP elegida THEN el listener de la LAN escucha en `<ip>:41831` con TLS y la huella coincide con `lan-cert.pem`; el local sigue igual.
- **AC-3**: Given un PIN generado en la app When un dispositivo manda `POST /pair` con ese PIN Then recibe su token y la huella; el mismo PIN no sirve dos veces, vence a los 5 min y 5 intentos fallidos lo anulan con 429.
- **AC-4**: WHEN una petición a la LAN llega sin token, con uno revocado o con el token local THEN 401.
- **AC-5**: WHEN un dispositivo pide una ruta administrativa (motores, almacenamiento, ajustes, `/fs`, Biblioteca, carpetas de entrada, emparejamiento) THEN 404.
- **AC-6**: WHEN un dispositivo sube un archivo y encola `media.convert` con `upload:<id>` THEN el trabajo usa esa subida; con una ruta de esta PC, 403 `remote_path_not_allowed`; con un `kind` fuera de `REMOTE_KINDS`, 403; con un archivo sobre el tope, 413.
- **AC-7**: WHEN un dispositivo lista trabajos o pide `/files` THEN solo ve los suyos y sus salidas; los de otro dan 404.
- **AC-8**: WHEN un cliente MCP de otro equipo se conecta a `https://<ip>:41831/mcp` con su token THEN lista las herramientas de la 029 menos `studio_watch_folder` y puede narrar; un `Origin` ajeno da 403.
- **AC-9**: WHEN se activa la red local THEN Windows pide elevación y queda la regla «Content Studio LAN» solo para el perfil Privado; si el usuario la rechaza, la app muestra `firewall_declined`; al desactivar, la regla se borra.
- **AC-10**: WHEN se abre Ajustes > Integraciones > Red local THEN se ven el interruptor, la dirección, la URL, la huella, «Emparejar dispositivo» con el PIN y su cuenta regresiva, y los dispositivos con «Revocar», en los tres idiomas.
- **AC-11**: Given la red local activa con `keep_awake` When pasa el tiempo de inactividad Then el server sigue encendido.

## 6. Debe sonar / no debe sonar

No aplica: la spec no cambia cómo se genera el audio.

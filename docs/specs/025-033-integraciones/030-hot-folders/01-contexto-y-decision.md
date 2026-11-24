# Spec 030: contexto y decisión

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación.
> Cada una queda anotada en [`docs/process/WARNING/`](../../../process/WARNING/README.md) (ficha `030-<tema>.md` con contexto, elegida, descartadas, cómo revertir y cómo comprobarla, y su fila en el README de la carpeta).
> Toda revisión pendiente queda en [`docs/process/PENDING/`](../../../process/PENDING/README.md) (ficha y fila, con qué la cierra).
>
> **Datos del usuario: solo los que crea esta spec**. La spec no borra ni sobrescribe voces grabadas (`server/data/narration/voz/`), voces construidas, salidas de `out/` ni modelos descargados que ella no creó. Sus pruebas escriben en carpetas nuevas (`out/<herramienta>/spec-030/` o `tmp/spec-030/`). Si algo parece exigir tocar datos existentes, no se decide al ejecutar: es un `blocked — user-data` y se pregunta. Los cambios locales o sin rastrear del checkout principal no son de la spec: no se tocan y no bloquean.

## 1. Precondición

```bash
git fetch origin dev
git log origin/dev --merges --oneline | grep -q 'feature/029-mcp' || echo FALLA
git cat-file -e origin/dev:server/src/content_studio/runtime/idle.py || echo FALLA
git cat-file -e origin/dev:server/src/content_studio/mcp_server/tools.py || echo FALLA
```

## 2. Contexto

Con la 028 y la 029, cualquier cliente que hable HTTP o MCP puede pedir trabajos. Muchas herramientas (grabadores, editores, exportadores, flujos de Power Automate) solo saben dejar un archivo en una carpeta. La Biblioteca ya tiene «carpetas vigiladas» (spec 020), pero solo para indexar, sin procesar nada y sin watcher (`library/scan.py`).

### Términos

| Término | Significado | En el código |
| :--- | :--- | :--- |
| Carpeta de entrada | Carpeta registrada con una operación; lo que se suelta en ella se procesa | tabla `inbox_folders` |
| Recibo | `<nombre>.result.json` o `<nombre>.error.json` | `inbox/receipts.py` |
| Estable | Mismo tamaño y fecha en dos sondeos seguidos | `inbox/scanner.py` |

### Hallazgos de la exploración

- **Carpetas vigiladas de la Biblioteca** solo indexan, sin watcher (`server/src/content_studio/library/scan.py`, docstring).
- **Validación por servicio**: `queue.enqueue` llama a `validate(params)` y lanza `InvalidJob` con `errors` (`jobs/queue.py`).
- **Eventos del worker**: el `Broker` publica cada cambio de un trabajo (`api/events.py`): sirve para los recibos.
- **Migraciones**: lista de SQL según `PRAGMA user_version` (`db/schema.py`, `migrate`).
- **watchdog 7.1.1** exige Python ≥ 3.11 y avisa los eventos perdidos con `EventsLostEvent` (PyPI y changelog, 2026-11-24).

## 3. Solución

- Paquete `inbox/` (stdlib): tablas, parámetro de entrada por operación, sondeo y recibos.
- API `/inbox/folders`, CLI `studio inbox` y herramienta MCP `studio_watch_folder`.
- En Ajustes > Integraciones, «Carpetas de entrada».

Cada decisión pasa por la escalera de plan-format.md §0 (¿debe existir? ¿ya existe? ¿stdlib o una dependencia que ya está?).

- **D-1: Carpetas registradas por el cliente** — El usuario lo pidió: «donde lo indique el cliente». Se descarta una sola `inbox/` fija en la carpeta de salidas.
- **D-2: Sondeo con `os.scandir`** — `watchdog` 7 exige Python 3.11 en su rama nueva y `ReadDirectoryChangesW` pierde eventos al desbordarse (investigación §4); unas decenas de archivos por carpeta no justifican una dependencia, y el sondeo funciona igual en OneDrive y en red. Se descarta `watchdog` o `watchfiles`, porque igual exigen reescanear y suman una dependencia.
- **D-3: Subcarpetas y recibos** — Es la convención de Adobe Media Encoder y de los flujos de carpeta caliente: el que soltó el archivo espera el resultado al lado. El trabajo sigue en `out/` y en la Biblioteca; a `done/` va una copia. Se descarta solo el recibo con rutas a `out/`, porque obliga al cliente a leer JSON para encontrar el archivo.
- **D-4: Carpetas y apagado por inactividad** — El usuario quiere que el server se apague sin uso (028, D-5), pero nadie lo despierta al soltar un archivo; así cada carpeta elige. Se descarta despertar el server con un vigilante aparte, porque sería otro proceso residente.
- **D-5: Registrar desde el MCP** — Un agente puede preparar el flujo («todo lo que deje en esta carpeta conviértelo a MP3») sin abrir la app. Se descarta solo desde la app, porque deja afuera a los agentes.

## 4. Fuera de alcance

- Vigilar subcarpetas de forma recursiva: solo el primer nivel.
- Operaciones que necesitan varios archivos (unir, mezclar): van por `.job.json` con rutas, no por soltar.
- Carpetas en otro equipo de la LAN (032 sube archivos por HTTP).

## 5. Criterios de aceptación

- **AC-1**: WHEN se registra una carpeta existente con `kind` y `params` válidos (app, API o CLI) THEN queda en `GET /inbox/folders`; con una carpeta inexistente o `params` inválidos, 422 con el código.
- **AC-2**: Given una carpeta registrada con `media.convert` a MP3 When se suelta un `.wav` y queda estable Then se mueve a `processing/` y se encola un trabajo.
- **AC-3**: WHEN un archivo sigue creciendo entre sondeos o termina en `.part` o `.tmp` THEN no se toma.
- **AC-4**: WHEN el trabajo termina THEN `done/<nombre>/` tiene el original, las salidas y `<nombre>.result.json` con `job_id` y rutas.
- **AC-5**: WHEN el trabajo falla THEN `failed/<nombre>/` tiene el original y `<nombre>.error.json` con `code` y `message`.
- **AC-6**: WHEN se suelta un `<nombre>.job.json` con `kind` y `params` (rutas relativas a la carpeta) THEN se encola con esos parámetros; si son inválidos, va a `failed/` con los errores.
- **AC-7**: Given archivos ya procesados y otros soltados con el server apagado When el server arranca Then procesa solo los nuevos.
- **AC-8**: Given una carpeta con `keep_awake` When pasa el tiempo de inactividad Then el server sigue encendido; sin `keep_awake`, se apaga.
- **AC-9**: WHEN se abre Ajustes > Integraciones THEN se pueden agregar (elegir carpeta, operación y opciones), pausar y quitar carpetas de entrada, en los tres idiomas.
- **AC-10**: WHEN un agente llama `studio_watch_folder` THEN la carpeta queda registrada, y la lista de herramientas MCP tiene once.

## 6. Debe sonar / no debe sonar

| Salida | Debe | No debe |
| :--- | :--- | :--- |
| `done/<nombre>/<nombre>.mp3` de un `.wav` de prueba (`tmp/spec-030/`) | La misma duración que el original (±0,1 s) | Cortes, silencio |

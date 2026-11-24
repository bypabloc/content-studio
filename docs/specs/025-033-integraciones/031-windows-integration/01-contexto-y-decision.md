# Spec 031: contexto y decisión

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación.
> Cada una queda anotada en [`docs/process/WARNING/`](../../../process/WARNING/README.md) (ficha `031-<tema>.md` con contexto, elegida, descartadas, cómo revertir y cómo comprobarla, y su fila en el README de la carpeta).
> Toda revisión pendiente queda en [`docs/process/PENDING/`](../../../process/PENDING/README.md) (ficha y fila, con qué la cierra).
>
> **Datos del usuario: solo los que crea esta spec**. La spec no borra ni sobrescribe voces grabadas (`server/data/narration/voz/`), voces construidas, salidas de `out/` ni modelos descargados que ella no creó. Sus pruebas escriben en carpetas nuevas (`out/<herramienta>/spec-031/` o `tmp/spec-031/`). Si algo parece exigir tocar datos existentes, no se decide al ejecutar: es un `blocked — user-data` y se pregunta. Los cambios locales o sin rastrear del checkout principal no son de la spec: no se tocan y no bloquean.

## 1. Precondición

```bash
git fetch origin dev
git log origin/dev --merges --oneline | grep -q 'feature/030-hot-folders' || echo FALLA
git cat-file -e origin/dev:server/src/content_studio/inbox/scanner.py || echo FALLA
```

## 2. Contexto

La app es una ventana de Tauri con instalador NSIS por usuario. No registra ningún esquema de URL, no aparece en el menú del Explorador y no arranca con Windows. Desde la 028 el server vive aparte de la ventana y desde la 030 hay carpetas que necesitan el server encendido.

### Términos

| Término | Significado | En el código |
| :--- | :--- | :--- |
| Enlace externo | Una URL `content-studio://` o los argumentos `--send` que llegan del SO | `ExternalRequest` |
| Instancia única | Una sola ventana: un segundo arranque pasa sus argumentos a la primera | `tauri-plugin-single-instance` |
| «Enviar a» | Menú del Explorador alimentado por los accesos directos de `%APPDATA%\Microsoft\Windows\SendTo` | D-3 |

### Hallazgos de la exploración

- **Sin plugins de enlace ni de instancia única**: `client/src-tauri/Cargo.toml` tiene dialog, opener, notification, window-state, updater y process.
- **Hook NSIS existente**: `bundle.windows.nsis.installerHooks = "installer/nsis/hooks.nsh"` en `tauri.conf.json`.
- **Secciones**: la lista de `client/src/app/nav.ts` (una línea por sección).
- **Crate `windows`** ya está en el `Cargo.toml` (Job Objects); suma la feature del registro.
- **Deep link en Windows**: el SO lanza un proceso nuevo con la URL y hay que activar la feature `deep-link` de single-instance ([Tauri](https://v2.tauri.app/plugin/deep-linking/)).

## 3. Solución

- Plugins de enlace e instancia única; Rust reenvía `argv` a la ventana.
- `parseExternal` (pura) y `useExternalRequests` en el client.
- Accesos directos de «Enviar a» en el hook NSIS.
- Interruptor «Iniciar el servidor con Windows».

Cada decisión pasa por la escalera de plan-format.md §0 (¿debe existir? ¿ya existe? ¿stdlib o una dependencia que ya está?).

- **D-1: Plugins oficiales de Tauri** — En Windows el SO lanza otro proceso con la URL; el plugin la reenvía a la ventana abierta (investigación §5). Registra en HKCU, sin admin. Se descarta registrar el esquema a mano en NSIS, porque igual hace falta la instancia única.
- **D-2: Enlaces sin efectos** — Cualquier página o proceso puede abrir una URL; encolar un trabajo de GPU o escribir en disco desde ahí sería un vector de abuso. Se descarta encolar con un diálogo de confirmación, porque el diálogo se acepta por costumbre.
- **D-3: «Enviar a»** — Es lo más barato: sin registro ni admin, y se borra con la desinstalación. El menú moderno exige `IExplorerCommand`, un paquete *sparse* con identidad y una DLL COM, sin una vía NSIS verificada (investigación §5). Se descarta verbos clásicos en `HKCU\Software\Classes\*\shell`, que aparecen igual que «Enviar a» dentro de «Mostrar más opciones» y ensucian el menú de cada archivo.
- **D-4: Inicio al iniciar sesión** — Las carpetas de entrada con `keep_awake` y los asistentes necesitan el server sin abrir la app; `pythonw` no abre consola y `api up` respeta la instancia única (028). Se descarta una tarea programada, porque pide más permisos y es más difícil de deshacer.

## 4. Fuera de alcance

- El menú contextual moderno de Windows 11 (D-3).
- Asociaciones de archivo y «Abrir con».
- Enlaces que encolan sin confirmación (D-2).
- macOS y Linux: el esquema se registra igual, pero solo se prueba en Windows.

## 5. Criterios de aceptación

- **AC-1**: WHEN se abre `content-studio://open/music` THEN la app (abierta o no) muestra Música.
- **AC-2**: WHEN se abre `content-studio://job/<id>` o `library/<id>` THEN se ve su detalle; con un id inexistente, el error de la API y la cola.
- **AC-3**: WHEN se abre `content-studio://new/narration?text=Hola&voice=<v>` THEN Narración muestra el texto y la voz y no hay trabajos nuevos hasta pulsar Generar.
- **AC-4**: WHEN llega una URL con una acción, un `kind` o un parámetro fuera de la lista, una ruta inexistente o más de 4096 caracteres THEN se ignora con el aviso `deeplink.invalid` y no se llama a la API.
- **AC-5**: Given la ventana abierta When se abre un enlace o «Enviar a» Then no aparece otra ventana: la abierta recibe el pedido y pasa al frente.
- **AC-6**: WHEN se instala la app THEN existen los cinco accesos directos en `SendTo`; WHEN se desinstala THEN no queda ninguno.
- **AC-7**: WHEN se envían tres archivos con «Content Studio - Convertir a MP3» THEN hay tres trabajos `media.convert` en la cola y el aviso dice 3; uno inexistente se salta y se cuenta.
- **AC-8**: WHEN se activa «Iniciar el servidor con Windows» THEN existe `HKCU\Software\Microsoft\Windows\CurrentVersion\Run\ContentStudioServer` con `pythonw.exe -m content_studio api up`; al apagarlo, se borra.

## 6. Debe sonar / no debe sonar

No aplica: la spec no cambia cómo se genera el audio.

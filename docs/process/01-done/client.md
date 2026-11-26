---
modulo: cliente
actualizada: 2026-11-25
---

# Cliente de escritorio (Tauri)

## Qué resuelve

La ventana de escritorio Content Studio: levanta el server, muestra la barra lateral con las secciones, la cola de trabajos con su progreso en vivo y los ajustes. Es la base donde cada spec agrega su sección.

## Qué hace hoy

- Tauri 2 se adjunta al server compartido con `studio api up --with-token` (spec 028): no lo posee, así que el server sobrevive a la ventana. Antes de instalar una actualización detiene el server (`api down --force`).
- Ajustes > Integraciones: dirección, puerto, minutos sin uso, copiar el token y cambiarlo. Cambiarlo detiene el server y la app reconecta con `get_connection`. Un fallo de red pide la conexión otra vez y repite la llamada una vez.
- La API se pide con un cliente tipado desde OpenAPI (`shared/api/schema.d.ts`) y TanStack Query. Los eventos SSE actualizan la caché sin volver a pedir datos.
- Cola: ver, reordenar con el ratón o el teclado (anuncios en español), pausar, cancelar y reintentar. Al terminar un trabajo avisa con un toast, y sin foco también con notificación y sonido (desactivables).
- Selectores con ★ en la opción recomendada que recuerdan la última elección (tabla `settings`).
- Ajustes: tema claro, oscuro o del sistema; avisos; restablecer elecciones y atajos (Ctrl+K, Ctrl+Enter, Espacio).
- Idioma: Español, English y Português, elegido en Ajustes (Sistema lleva la ★; el valor se guarda en `ui.language` y el primer cuadro ya sale en ese idioma). Cambia sin recargar.
- Los textos visibles salen del catálogo único con `t()`. La etapa `i18n` bloquea los textos sueltos en el código, y el lint no deja literales en JSX.
- La UI se arma con componentes en tres niveles (átomos, moléculas y organismos; `features/` y `app/` solo los usan). La etapa `ui-structure` bloquea una etiqueta HTML nativa fuera de un átomo, y oxlint bloquea los imports que saltan la jerarquía (D-4).
- La barra (`UIAppShell`) muestra las secciones, la cola bajo ellas y el tema y la versión al pie. Se colapsa a iconos con el botón o con `Ctrl+B`, y el estado se recuerda.
- Iconos: la cola, el tema, la barra, la paleta, Narración y Ajustes usan `UIIcon`. Cada botón de solo ícono (`UIIconButton`, o el trigger de la barra dentro de `UITooltip`) muestra su texto de ayuda, y sus nombres están en `action.*`. El criterio de cuándo va solo con ícono está en `.agents/rules/ui-components.md`.

## Dónde vive

- Código: `client/src/{app,features,shared}`. Componentes en `shared/components/{shadcn,atoms,molecules,organisms}`, formularios en `shared/forms/`, tokens y estilos en `styles/`, e idioma en `shared/i18n/`. El Rust está en `client/src-tauri/src/` (`server.rs`, `lib.rs` y sus pruebas en `tests.rs`).
- Textos: `server/src/content_studio/messages/{es,en,pt}.json`, con el alias `@messages`.
- Gates: `client-lint` (con la jerarquía de imports), `client-typecheck`, `client-unit` (con la auditoría del espejo y la cobertura), `ui-structure` (etiquetas nativas), `budget` (`client/budget.json`, 228 kB), `i18n` (catálogos, claves en uso y textos sueltos), `e2e` (`tests/e2e/`) y `tauri-check` (`cargo check`).

## Historial

- 2026-11-19: ficha inicial con la spec 005 (client Tauri base: shell, tema, cola, selector y ajustes).
- 2026-11-19: spec 007 (i18n): catálogo único en tres idiomas, selector de idioma en Ajustes y etapa `i18n`.
- 2026-11-20: spec 008 (componentes atómicos): 77 componentes de klinikae en átomos, moléculas y organismos; `UIAppShell`, `useForm` y las etapas `ui-structure` y de jerarquía.
- 2026-11-20: spec 009 (iconos): mapa de `UIIcon` con los nombres de content-studio, iconos de estado en la cola, selector de tema con íconos y el criterio de solo ícono.
- 2026-11-20: spec 010 (client): «Mis voces», asistente de grabación con indicador «Micrófono en uso», región de la onda al importar, micrófono y registro en Ajustes, y borrar tomas a la papelera (PR #80).
- 2026-11-25: spec 027 (dependencias): JavaScript y crates en su última versión estable, exactas; `getrandom` 0.4; TypeScript se queda en 5.9.3; edición 2024; la CSP permite el IPC de Tauri.
- 2026-11-25: spec 028 (server compartido): la ventana se adjunta y no lo posee; Ajustes > Integraciones; reconexión tras la inactividad.
- 2026-11-25: spec 036 (sección Transcripción): «Identificar hablantes» con leyenda editable, texto por bloques, exportar TXT y crear subtítulos. Ficha: `transcription.md`.

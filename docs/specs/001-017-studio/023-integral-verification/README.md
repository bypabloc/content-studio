# 023: verificación integral del lote y cierre

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación.
> Cada una queda anotada en [`docs/process/WARNING/`](../../../process/WARNING/README.md) (ficha `023-<tema>.md` con contexto, elegida, descartadas, cómo revertir y cómo comprobarla, y su fila en el README de la carpeta).
> Toda revisión pendiente queda en [`docs/process/PENDING/`](../../../process/PENDING/README.md) (ficha y fila, con qué la cierra).
>
> **Datos del usuario: solo los que crea esta spec**. La spec no borra ni sobrescribe voces grabadas, voces construidas, salidas de `out/` ni modelos descargados que ella no creó. El recorrido usa un perfil de voz `spec-023` y una carpeta de proyecto nueva. **No fusiona `dev` en `main` ni publica un Release** sin la aprobación del usuario.

| Campo | Valor |
| :--- | :--- |
| Tipo | chore |
| Escala | Micro en código (solo los fixes que salgan), con verificación integral |
| Rama | `chore/023-integral-verification` desde `origin/dev`, en `../content-studio-worktrees/023-integral-verification/` |
| Depende de | [022](../022-installer/README.md) (fusionada en `origin/dev`), es decir, todo el lote |
| Origen | Pedido del usuario (lote [001-017-studio](../README.md)) |

## Objetivo

Comprobar que el estudio completo funciona de punta a punta en la app **instalada**, con un video real hecho de principio a fin, y entregar al usuario un único informe con las mediciones y las rutas de cada salida para que escuche y revise. Después, cerrar el lote: fichas, `docs/process/`, borrar la carpeta del lote y dejar el PR `dev → main` listo, sin fusionarlo.

## Contexto y decisión

* Lo que cubre el lote: server y devtools (001), inglés y cspell (002), test-runner (003), API y cola (004), client (005), Narración (006), catálogo único de textos con i18n en es, en y pt (007), componentes con Atomic Design y bloqueo de etiquetas nativas (008), iconos (009), Voces y Grabar (010), Música (011), Motores y Almacenamiento (012), Limpiador (013), Subtítulos (014), Convertir y Normalizar (015), Mezcla (016), Editor (017–019), Biblioteca (020), asistente con LLM local (021) e instalador (022).
* **D-1**: el recorrido es un caso real encadenado (decisión del usuario) y no una batería por sección, porque es lo que detecta los fallos de integración entre secciones.
* **D-2**: los fallos que aparezcan se corrigen en esta misma rama con commits `fix(<área>): …` y un test de regresión en el espejo del módulo, o en `integration/test_bugs.py` si cruza módulos. Si un fallo es grande (más de 2 archivos de código), se anota en `PENDING/023-<tema>.md` y se abre una spec nueva, sin inflar esta.
* **D-3**: el cierre deja el PR `dev → main` abierto, con el resumen, sin fusionarlo. El tag `v0.1.0` y el Release los decide el usuario.
* **Fuera de alcance**: funciones nuevas, ajustes de gusto que no pidió el usuario y publicar el Release.

### Criterios de aceptación

* **AC-1**: WHEN se corre `test-runner --type=all,e2e,tauri-check,budget,guard-tdd` sobre `origin/dev` THEN todo pasa.
* **AC-2**: WHEN se recorre el flujo de §Verificación en la app instalada THEN cada paso produce su salida y cada medición está dentro del «debe sonar» de su spec.
* **AC-3**: WHEN se revisa `docs/process/` THEN `01-done/` tiene una ficha por módulo nuevo (server, client, voices, engines, cleaner, subtitles, convert, edit, mix, editor, library, llm e installer), cada ficha WARNING del lote tiene su fila, no queda ningún PENDING cerrable sin cerrar, y `docs/specs/001-017-studio/` ya no existe.
* **AC-4**: WHEN se corren `agent-context` y `rules` y la validación headless THEN pasan, y `AGENTS.md` describe la estructura final (`server/`, `client/`, `devtools/` y `tests/`) sin rutas viejas.

## Plan

| Tarea | Qué | AC | Verify | Done |
| :--- | :--- | :--- | :--- | :--- |
| T1 | Batería completa sobre `origin/dev` | AC-1 | `test-runner` | [ ] |
| T2 | Build e instalación (carpeta o usuario de prueba) | AC-2 | §Verificación 1 | [ ] |
| T3 | Recorrido encadenado con mediciones | AC-2 | §Verificación 2 | [ ] |
| T4 | Fixes que salgan (TDD por cada uno) | AC-2 | `test-runner` | [ ] |
| T5 | Informe para el usuario | AC-2 | `tmp/spec-023/report.md` | [ ] |
| T6 | Cierre de `docs/process/`, reglas y `AGENTS.md` | AC-3, AC-4 | `agent-context`, `rules` | [ ] |
| T7 | Borrar la carpeta del lote y su fila del índice | AC-3 | `git status` | [ ] |
| T8 | PR a `dev`, merge y PR `dev → main` en espera | — | `gh pr checks` | [ ] |

Commits: `fix(<área>): …` por cada fallo (si los hay), `docs: cierre del lote 001-022 en docs/process` y `docs: se borra la carpeta del lote 001-022`.

## Verificación

1. **Build e instalación**: `tauri build`, instalar en un usuario o carpeta de prueba, primer arranque y bienvenida. Instalar el paquete recomendado (VoxCPM2, ACE-Step, faster-whisper large-v3-turbo y el LLM ★ de la 021) en la carpeta de prueba (en segundo plano, con el log en `logs/`).
2. **Recorrido** (con el turno de GPU para cada paso que carga un modelo; las corridas largas en segundo plano):
   1. **Voz**: crear el perfil `spec-023` e importar un tramo de 10 s de un video con permiso (o grabar `neutral` y `expert` con el micrófono), con el chequeo `ok`.
   2. **Narración**: un guion de 4 párrafos con el editor (los avisos funcionan) y «Revisar con IA» (aceptar parte del diff), voz `spec-023` o una del catálogo, Evaluar activo. Regenerar un párrafo y elegir la toma en Comparar.
   3. **Música**: «Generar música para esta voz» desde Mezcla, con 2 variantes y la elegida con ★. Duración exacta.
   4. **Mezcla** con ducking por transcripción a -14 LUFS.
   5. **Video**: un video crudo con silencios (del usuario o grabado). **Limpiador** con revisión y render.
   6. **Mezcla sobre video**: la música de 3 en `under` del video limpio.
   7. **Subtítulos** desde el Limpiador: «Corregir transcripción» con un glosario, «Sugerir palabras clave», estilo `reels` y **quemado**. Traducir la pista al portugués con el LLM.
   8. **Convertir** a Reels con `follow-face` y **normalizar** a -14.
   8b. **Editor**: «Abrir en Editor» el video convertido; sumar el logo con transparencia que entra con keyframes, un título `lower-third`, una transición `fade` y la voz de 1 grabada encima de la mezcla en una pista nueva; exportar a MP4 con normalizar y «Mandar a Subtítulos».
   9. **Publicar** (021): títulos, descripción, hashtags y capítulos del video final para YouTube y Reels.
   10. **Biblioteca**: encontrar todo lo anterior por proyecto (crear el proyecto «spec-023» y agregar las salidas), buscar un texto del guion con «Buscar en el contenido», «Editar y repetir» sobre la música y mandar a la papelera las tomas no elegidas **de esta spec**.
3. **Mediciones** de cada salida (`verify-before-claiming-done.md` §2): duración, LUFS y TP, y en los videos, resolución, fps, sincronía y codificador. Espectrogramas de la narración, la música, la mezcla y el audio del video final en `tmp/spec-023/`, más cuadros del video final. Todo lo revisa `image-reader` contra el «debe sonar» de cada spec.
4. **Informe** `tmp/spec-023/report.md`: una tabla por paso con la salida (ruta clicable), las mediciones, el resultado y las capturas. Va completo en el mensaje final al usuario y en el cuerpo del PR `dev → main`.

## Cierre

1. Se actualizan las fichas de `docs/process/01-done/` y se revisan `WARNING/` (lo que bloquea el pase a `main` queda listado en el PR) y `PENDING/`.
2. `git rm -r docs/specs/001-017-studio/` y su fila de `docs/specs/README.md`, con el próximo número libre en 020.
3. PR `chore/023-integral-verification` a `dev`, checks y merge. Después, `worktree close 023-integral-verification`.
4. `gh pr create --base main --head dev --title "release: content-studio como estudio de escritorio (lote 001-022)"`, con el informe, las fichas WARNING que bloquean y los pasos para publicar (`devtools version 0.1.0` y el tag). **No se fusiona**: `Status: done` del lote y se le entrega el PR al usuario.

## WARNING y PENDING

* WARNING: los que salgan de los fixes (`023-<tema>.md`), o «ninguna».
* PENDING: los fallos grandes que se pasen a spec nueva, o «ninguna».

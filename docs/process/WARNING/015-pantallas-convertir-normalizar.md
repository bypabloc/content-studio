# 015: pantallas Convertir y Normalizar (T7)

**Qué se decidió.**

- **Recortar y unir sin pantalla** (D-6). El plan creaba `features/edit/`; la spec dice que la pantalla la absorbe el Editor (017–019), así que no se crea. Los trabajos `media.trim`, `media.concat` y `media.split` se prueban por la API.
- **Un solo selector de formato** con «Redes» como una opción más (`social`). Al elegirla aparecen el preset de red (★ por la proporción de la fuente) y el encuadre. `UISelect` no tiene grupos, así que el grupo (Audio, Video, GIF) va en la pista de cada opción.
- **Las rutas llegan por el arrastre de Tauri** (`useFilePaths`, con `onDragDropEvent` y el diálogo `open`, como `useScriptImport`). El arrastre HTML5 no da la ruta del disco, y el server la necesita para leer el archivo.
- **`GET /catalog/media?aspect=`** (servidor) sirve formatos, presets y el ★ de Redes según la proporción. Así el cliente no duplica la regla de `presets.recommended`.
- **`/media/info` da `width` y `height`** para un video (la proporción de la ★). Un audio trae `null`.
- **Un preset con encuadre sale a sus fps** (`-r`). El grafo del encuadre no cambia los cuadros, y sin esto un preset de 30 fps conservaba los de la fuente (AC-4 no se cumplía en las redes).
- **Un selector ★ compartido**: `useRecommendedValue` es la misma regla que usa `UIRecommendedSelect` (guardada si todavía existe, si no la recomendada). Las pantallas la usan para conocer la elección sin esperar a que el selector la informe.
- **El encuadre `manual` es un cuadro arrastrable** (`UICropArea`, organismo). Arranca centrado con la proporción del preset, y el arrastre se acota a la imagen. Las coordenadas van normalizadas (0 a 1).
- **`follow-face`** solo lanza el análisis (`media.reframe_track`) y espera el `track.json`. Dibujar la trayectoria sobre la línea de tiempo queda en PENDING.
- **Tabla de trabajos con `UITable`**, no con un `UIBatchTable` nuevo. Las dos tablas (Convertir y Normalizar) tienen columnas distintas, así que el paso de REFACTOR del plan no aplica.
- **Errores**: `UIErrorDetailDialog` (organismo sobre `UIDialog`) muestra el motivo y el detalle técnico. El motivo sale de `error.<código>` solo si el texto no lleva parámetros (`codec_unavailable` lleva `{codec}`, que el trabajo no guarda); si no, el texto genérico.
- **Catálogo**: claves compartidas `media.*` (archivos, estados, acciones, errores), y `convert.*` y `normalize.*` por pantalla. Las tres lenguas llevan las mismas claves.

**Verificado.**

- Servidor: `api` y `media` 204 pruebas en verde (las tres pruebas nuevas de catálogo, `-r` y dimensiones fallaban antes).
- Cliente: 195 archivos y 1096 pruebas en verde. `tsc --noEmit` limpio y oxlint sin errores.
- AC-10 (`ConvertPage.test.tsx`): cinco archivos y MP3 V2 encolan cinco trabajos con `{vbr: 2}`; la tabla muestra el progreso; un error abre el diálogo con el detalle técnico.
- AC-11 (`ReframePreview.test.tsx`): arrastrar 40 px de 400 en `manual` deja `x` en 0,4418 y `w` en 0,3164.

**Configuración que cambió para pasar el gate `all`.**

- **Presupuesto del bundle inicial: 234 → 236 kB gzip** (`client/budget.json`). El `es.json` se importa de forma estática (`shared/i18n/catalogs.ts`), así que las claves nuevas de Convertir, Normalizar y `media.*` suben la carga inicial en unos 0,96 kB. Las pantallas nuevas van en lazy.
- **Prefijos dinámicos del validador de i18n** (`tests/validators/i18n.json`): `convert.{channels,format,fps,group,preset,quality,rate,reframe,resolution}.` y `normalize.preset.`. Sus claves se eligen con `text(\`convert.format.${id}\`)`, que el validador no ve como `t('…')` literal. Cada prefijo tiene claves reales.
- **Palabras de cspell** (`cspell.config.yaml`, overrides de `messages/{es,en,pt}.json` y de `client/**`): `bitrate`, `kbps`, `vorbis` y `youtube`. Son nombres de códecs y unidades.
- **Cobertura de `edit.py`, `normalize.py` y `face_track_main.py`** (el gate exige 80 % por archivo; estaban en 67 %, 74 % y 60 %). Se añadieron pruebas unitarias que miran los argumentos del grafo de ffmpeg (sin ejecutarlo), la CLI de cada módulo, y la detección de caras con un `cv2` falso en `sys.modules` (OpenCV solo existe en `.venv-vision`).
- **Cobertura del cliente** (`Shell`, `ConvertPage`, `FormatPicker`, `ReframePreview`, `NormalizeListen`, `NormalizePage`): el gate exige 80 % por archivo en cada métrica. Se cubrieron los caminos que quedaban fuera (cancelar, reintentar, abrir la carpeta, elegir con el diálogo, rechazar un archivo, cerrar el error, preset personalizado, seguir a la persona, barras y desenfoque, el A/B de vuelta al original y la posición al cambiar de versión). Al cierre, la cobertura por archivo queda entre 81,8 % (ramas de `NormalizeListen`) y 100 % en líneas.
- **Tipos de la API regenerados** (`client/src/shared/api/schema.d.ts`, `gen:api`): el catálogo de medios y el parámetro `aspect` cambian el OpenAPI. La etapa `client-typecheck` compara con `git diff --quiet` contra el índice: el archivo regenerado tiene que estar en staging (`git add`) antes de correr `test-runner`, o la etapa falla aunque el contenido sea el correcto.
- **Espejos de prueba** que faltaban: `convertOptions`, `NormalizeListen`, `useRecommendedValue` y `formats`.

**Diferido.** Ver `docs/process/PENDING/015-trayectoria-y-ab-fuera-de-out.md`.

**Dónde.** `client/src/features/{convert,normalize}/`, `client/src/shared/{hooks,media,components/organisms}/`, `client/src/app/{nav.ts,Shell.tsx}`, `server/src/content_studio/api/routes/{catalog,media}.py`, `server/src/content_studio/media/convert.py`, y los tests espejo.

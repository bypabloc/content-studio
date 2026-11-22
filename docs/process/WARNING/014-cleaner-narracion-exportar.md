# 014: subtitular desde el limpiador y la narración, y exportar (ciclo 8)

**Qué se decidió.**

- **Video del limpiador**: «Subtitular» usa la última render `done` cuyo `params.analysis` es la carpeta de salida del job de análisis. No se liga por la carpeta del transcript: `analyze_main` deja el transcript en la caché de transcripción, así que esa carpeta no coincide. Toma `clean.mp4` (o `clean.wav` si la entrada es solo audio). Sin render, el botón espera (AC-11).
- **Palabras limpias**: `subtitles/create_main.clean_words` quita las palabras cuyo centro cae en un corte habilitado de `cuts.json` y remapea el resto con `clean.plan.remap`. La línea de tiempo del documento es la del video limpio.
- **Carpeta de los cortes**: el origen limpiador recibe `analysis` (la carpeta de salida del análisis) y lee el `cuts.json` de ahí. Antes lo buscaba junto al transcript, que está en la caché: en la app habría fallado con `FileNotFoundError`. El test de `create_main` ahora separa la caché del análisis; `validate` exige `analysis` (`missing_analysis`).
- **Narración**: el texto de los cues es el del guion (`script`, `language: 'es'`). Los tiempos salen de transcribir la toma y alinear el guion (D-4).
- **Importar**: `validate` rechaza con `unsupported_subtitle_format` cualquier archivo que no sea `.srt` o `.vtt`, antes de encolar.
- **Exportar**: `POST /subtitles/{id}/export` escribe `out/subtitles/<id>-<nombre>.<srt|vtt|ass>` y devuelve la ruta. ASS usa el preset clásico sobre el estilo del documento, con `PlayRes` 1920×1080.
- **Errores**: crear, exportar, quemar y traducir muestran el error con `toast.error`; el texto sale de `error.<código>` del catálogo.

**Verificado.** e2e: 44 pruebas en verde (AC-4, AC-6, AC-11 y los negativos). Server: 128 pruebas de subtítulos, API, servicios y limpiador en verde.

**Dónde.** `subtitles/create_main.py`, `subtitles/export.py`, `api/routes/subtitles.py`, `services/subtitles_create.py`, `client/src/features/cleaner/CleanReview.tsx`, `client/src/features/narration/NarrationResult.tsx`, `client/src/features/subtitles/SubtitlesEditor.tsx` y `SubtitlesPage.tsx`.

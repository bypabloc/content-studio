# 014 · Editor, vista previa y textos (ciclo 7, cliente)

Decisiones tomadas sin preguntar al usuario, dentro de la spec `docs/specs/001-017-studio/014-subtitles/`.

## Qué se decidió

- **JASSUB fijado a 2.5.36** (`bun add --exact`). Entra con `import()` diferido en `SubtitlesPreview.tsx` para no pesar en el arranque.
- **Cambiar la pista** es `renderer.renderer.setTrack(ass)`: la API pública de JASSUB expone el renderizador del worker como `Remote<ASSRenderer>` (Comlink), así que la llamada es asíncrona. `destroy()` también devuelve una promesa.
- **Autoguardado** de 1 s desde el último cambio (D-9), con un PUT del documento entero. En las pruebas se usan temporizadores reales y `waitFor`: con `vi.useFakeTimers()` los `findBy` agotan el tiempo.
- **Ícono del estado vacío** de «Subtítulos»: `narration` (AudioLines). `UIIcon` no tiene un ícono de subtítulos y no se añade uno solo para esto.
- **Textos**: 34 claves `subtitles.*` en `es`, `en` y `pt` (catálogo del server, orden alfabético). Ninguna lleva parámetros.
- **Líneas del encabezado ASS y nombres de fuente** (`ass.ts`, `presets.ts`) llevan `// i18n-ignore:`: son formato de archivo y nombres de fuente, no texto de interfaz.
- **Restricción de `features/`**: no se importa `UIBox`. El overlay de zonas y el contenedor de la vista previa usan `UIStack` con `className`.

## Correcciones que salieron al correr el gate

- Errores de mypy en código de commits anteriores de la 014: `cues` sin anotar (`subtitles/translate.py`), `project_id` sin tipar en `prepare` de `subtitles_burn` y `subtitles_translate` (ahora se comprueba `isinstance(int)` antes de consultar), y `store.get` que puede devolver `None` en `POST /subtitles` (ahora 404 `job_not_found`, igual que `jobs.py`).
- `jassub` y `tiktok` agregados a `devtools/cspell/content-studio-terms.txt` (términos técnicos en inglés).
- `schema.d.ts` regenerado con `gen:api`: solo suma líneas (264), sin borrar tipos existentes.

## Segunda pasada del gate

- **Presupuesto** `initialJsGzipKb` de 233 a 234: el catálogo `subtitles.*` y `nav.subtitles` (649 claves en `es`) suman
  al arranque, como en `013-presupuesto-js`. Comprobar: `python -m devtools test-runner --type=budget`.
- **Sección montada** en `Shell.tsx` con carga perezosa (`lazy`), entrada `subtitles` en `nav.ts` con el ícono `Captions`
  de lucide (nuevo en `UIIcon`). `nav.test.ts` fija la lista del nav (spec 009, AC-3) y ahora incluye la sección.
- **Tests espejo**: `SubtitlesPage`, `SubtitlesPreview` y `presets` (cliente); `services/test_subtitles_create.py`, movido
  desde `subtitles/` con `git mv`; el golden del ASS fundido en `test_ass.py`; `test_styles`, `test_burn_main` y
  `test_create_main` nuevos. La cobertura de `create_main` pasa del 69 % al mínimo del 80 %.

## Pendiente de este ciclo

- Escucha y render real de la vista previa con JASSUB en el navegador/Tauri: no se corrió aquí (requiere la app abierta con un video).
- Los tests del editor usan `t()` del catálogo real: si una clave falta, el test lo verá como texto literal.

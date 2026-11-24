# Spec 038: verificación final

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación.
> Cada una queda anotada en [`docs/process/WARNING/`](../../../process/WARNING/README.md) (ficha `038-<tema>.md` con contexto, elegida, descartadas, cómo revertir y cómo comprobarla, y su fila en el README de la carpeta).
> Toda revisión pendiente queda en [`docs/process/PENDING/`](../../../process/PENDING/README.md) (ficha y fila, con qué la cierra).
>
> **Datos del usuario: solo los que crea esta spec**. La spec no borra ni sobrescribe voces grabadas (`server/data/narration/voz/`), voces construidas, salidas de `out/` ni modelos descargados que ella no creó. Sus pruebas escriben en carpetas nuevas (`out/<herramienta>/spec-038/` o `tmp/spec-038/`). Si algo parece exigir tocar datos existentes, no se decide al ejecutar: es un `blocked — user-data` y se pregunta. Los cambios locales o sin rastrear del checkout principal no son de la spec: no se tocan y no bloquean.

## 1. Batería

| # | Comando | Aplica si |
| :--- | :--- | :--- |
| 1 | `uv run ruff check && uv run ruff format --check` | siempre |
| 2 | `python -m devtools test-runner --type=all` | siempre |
| 3 | `uv run pytest -m local` | siempre (libass y ffmpeg reales) |
| 4 | `python -m devtools test-runner --type=e2e` | siempre |
| 5 | `python -m devtools app-check run` (smoke) | siempre |

## 2. Comprobaciones propias

1. Subtítulos con hablantes desde el clip de 2 personas. Quemar en un video de prueba y extraer 3 cuadros con `ffmpeg -ss … -frames:v 1 tmp/spec-038/frame-<n>.png`. `image-reader` confirma los dos colores y que el texto se lee [AC-3].
2. Exportar SRT y VTT con nombres: abrir los archivos [AC-4].
3. El Editor con la mezcla transcrita con hablantes: la captura del carril la revisa `image-reader` [AC-7].
4. El Limpiador con hablantes y «Subtitular»: el proyecto conserva los hablantes en el tiempo limpio, revisando 5 cues contra el audio [AC-8].
5. Un proyecto de subtítulos viejo, sin hablantes, abre, exporta y quema igual que antes [AC-1].

Sin el motor instalado: `PENDING/038-corrida-real` y se sigue.

## 3. Escucha

No aplica (el audio no cambia). Las rutas del video quemado van al PR para que el usuario lo vea.

## 4. Cierre, PR y merge

- [ ] Fichas `WARNING/038-*`.
- [ ] `01-done/subtitles.md`, `editor.md` y `cleaner.md` actualizadas.
- [ ] Fases y fila del lote en `IMP`.
- [ ] `git fetch origin dev`, un push, PR, checks, `gh pr merge --merge` y `worktree close 038-speakers-everywhere`.

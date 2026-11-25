# 037: decisiones de la sección Hablantes (fase 2)

- **Contexto**: al guardar un nombre, el borrador de la fila de la leyenda y el nombre guardado pueden quedar distintos. Con un guardado optimista que falla, la caché vuelve al nombre anterior en el mismo lote de React: la fila no ve cambiar el nombre y conserva el texto no guardado.
- **Elegida**: un guardado fallido vuelve a montar la leyenda (`key` con `legendRev`), así el borrador toma el nombre guardado. El mapa entero se guarda con `PUT /jobs/{id}/speakers`, como Transcripción (036).
- **Descartadas**: rollback solo con `setQueryData` (no reinicia el borrador); no guardar al instante (la línea de tiempo y la leyenda esperan al servidor).
- **Cómo revertir**: quitar `legendRev` y el `key` de `UISpeakerLegend` en `SpeakerResult.tsx`; la prueba «WHEN a rename cannot be saved» vuelve a fallar.
- **Cómo comprobarla**: `bun run --cwd client test -- SpeakerResult`.

- **Contexto**: `diarize.split` escribe los WAV en la carpeta de su propio trabajo, no en la de la diarización; la versión de F1 los buscaba en `speakers/` dentro de la carpeta de turnos y nunca los encontraba (AC-5).
- **Elegida**: el audio por hablante se busca en el último `diarize.split` terminado cuyo parámetro `turns` apunta a la carpeta de la diarización (`output_dir` de ese trabajo).
- **Descartadas**: una carpeta fija dentro de la diarización (no existe); guardar la ruta de los WAV en `speakers.json` (duplica lo que ya tiene el trabajo).
- **Cómo revertir**: volver a `_split(folder)` de F1 en `server/src/content_studio/api/routes/diarizations.py`.
- **Cómo comprobarla**: `uv run pytest server/tests/unit/src/content_studio/api/routes/test_diarizations.py` (el caso con `wavs`).

- **Contexto**: AC-6 pide que el Editor abra el proyecto enviado en `?project=`.
- **Elegida**: el Editor lee el parámetro una vez, al montar (`useEffect` sin dependencias), igual que el resto de parámetros de sección.
- **Descartadas**: escuchar `hashchange` dentro del Editor (el Editor no siempre está montado al llegar el hash, y el resto de secciones no lo hacen).
- **Cómo comprobarla**: `bun run --cwd client test -- EditorPage` (el caso «WHEN the hash names a project»).

- **Contexto**: el umbral de cobertura del client es 80 % por archivo. `SpeakerResult.tsx` no estaba en el plan de pruebas y quedaba en 65 % de ramas.
- **Elegida**: `client/tests/unit/src/features/speakers/SpeakerResult.test.tsx` con los estados (error, cancelado, sin habla, video, foco, rollback y separación).
- **Descartadas**: bajar el umbral (no se hace) o excluir el archivo (oculta el código de la sección).

- **Contexto**: la e2e de Chromium no dibuja regiones de la onda con el archivo de prueba, así que no puede comprobar las flechas ←/→.
- **Elegida**: las flechas se prueban en `SpeakerTimeline.test.tsx`; la e2e comprueba el enfoque por el selector y el nombre del hablante.
- **Cómo comprobarla**: `bun run --cwd client test -- SpeakerTimeline`.

- **Contexto**: el escenario de app-check de Hablantes no encola trabajos, igual que el de Transcripción (036).
- **Elegida**: el escenario recorre la sección en claro y en oscuro. La identificación real con pyannote va a `PENDING/037-corrida-real`.
- **Pendiente**: [037-corrida-real](../PENDING/037-corrida-real.md).

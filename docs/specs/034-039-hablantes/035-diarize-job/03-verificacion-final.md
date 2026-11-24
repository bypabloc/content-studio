# Spec 035: verificación final

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación.
> Cada una queda anotada en [`docs/process/WARNING/`](../../../process/WARNING/README.md) (ficha `035-<tema>.md` con contexto, elegida, descartadas, cómo revertir y cómo comprobarla, y su fila en el README de la carpeta).
> Toda revisión pendiente queda en [`docs/process/PENDING/`](../../../process/PENDING/README.md) (ficha y fila, con qué la cierra).
>
> **Datos del usuario: solo los que crea esta spec**. La spec no borra ni sobrescribe voces grabadas (`server/data/narration/voz/`), voces construidas, salidas de `out/` ni modelos descargados que ella no creó. Sus pruebas escriben en carpetas nuevas (`out/<herramienta>/spec-035/` o `tmp/spec-035/`). Si algo parece exigir tocar datos existentes, no se decide al ejecutar: es un `blocked — user-data` y se pregunta. Los cambios locales o sin rastrear del checkout principal no son de la spec: no se tocan y no bloquean.

## 1. Batería

| # | Comando | Aplica si |
| :--- | :--- | :--- |
| 1 | `uv run ruff check && uv run ruff format --check` | siempre |
| 2 | `python -m devtools test-runner --type=all` | siempre |
| 3 | `uv run pytest -m local` | siempre (venv de `pyannote` y ffmpeg real) |
| 4 | `python -m devtools agent-context && python -m devtools rules` | toca `AGENTS.md` |
| 5 | `uv run studio diarize <clip> --speakers 2` (toma el candado solo) | siempre |
| 6 | Duración, LUFS y espectrograma de `speakers/*.wav` en `tmp/spec-035/`, revisados por `image-reader` | siempre |
| 7 | `uv run studio diarize --help`, un caso real y uno de error, sin TTY | siempre |

## 2. Comprobaciones propias

Clips de prueba: dos clips de 2 a 5 min con 2 y 3 personas, con permiso de sus dueños, copiados a `tmp/spec-035/`. Si no hay clips propios, se arma uno con dos voces del catálogo de narración que se alternan.

1. `studio diarize` con cada clip. Hay que registrar:
   * el pico de VRAM con `nvidia-smi --query-gpu=memory.used --format=csv -lms 500` en segundo plano, con la salida en `logs/spec-035-vram.log`;
   * el tiempo.

   Si el pico pasa de 3 GB, se baja `embedding_batch_size` y se registra en `WARNING/035-batch-de-embeddings` [AC-4, AC-7].
2. Repetir el mismo archivo: termina en menos de 2 s y el log no carga el pipeline [AC-8].
3. `transcribe` con `diarize: true` sobre el clip de 2 personas. Revisar a mano 50 palabras: el porcentaje con hablante equivocado (WDER aproximado) va al reporte [AC-1, AC-9].
4. `diarize.split`: los WAV duran lo mismo que el original. Escuchar que cada uno tenga solo su voz [AC-5].
5. Verificar el motor desde la app: pasa [AC-6].

Si el motor no está instalado por falta del token: `PENDING/035-corrida-real` y se sigue.

## 3. Escucha

Las rutas de `speakers/*.wav` van al reporte y al PR para que el usuario escuche.

## 4. Cierre, PR y merge

- [ ] Fichas `WARNING/035-*` con lo medido.
- [ ] `docs/process/01-done/diarization.md` creada.
- [ ] Fases en `IMP` y la fila 035 del lote en `IMP`.
- [ ] `git fetch origin dev`, merge si avanzó, un push, PR, `gh pr checks --watch` y `gh pr merge --merge`.
- [ ] `python -m devtools worktree close 035-diarize-job`.

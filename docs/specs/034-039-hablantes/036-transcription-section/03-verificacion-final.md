# Spec 036: verificación final

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación.
> Cada una queda anotada en [`docs/process/WARNING/`](../../../process/WARNING/README.md) (ficha `036-<tema>.md` con contexto, elegida, descartadas, cómo revertir y cómo comprobarla, y su fila en el README de la carpeta).
> Toda revisión pendiente queda en [`docs/process/PENDING/`](../../../process/PENDING/README.md) (ficha y fila, con qué la cierra).
>
> **Datos del usuario: solo los que crea esta spec**. La spec no borra ni sobrescribe voces grabadas (`server/data/narration/voz/`), voces construidas, salidas de `out/` ni modelos descargados que ella no creó. Sus pruebas escriben en carpetas nuevas (`out/<herramienta>/spec-036/` o `tmp/spec-036/`). Si algo parece exigir tocar datos existentes, no se decide al ejecutar: es un `blocked — user-data` y se pregunta. Los cambios locales o sin rastrear del checkout principal no son de la spec: no se tocan y no bloquean.

## 1. Batería

| # | Comando | Aplica si |
| :--- | :--- | :--- |
| 1 | `uv run ruff check && uv run ruff format --check` | siempre |
| 2 | `python -m devtools test-runner --type=all` | siempre |
| 3 | `python -m devtools test-runner --type=e2e` | siempre |
| 4 | `python -m devtools app-check run` (smoke) y un escenario `tests/e2e/app-check/transcription.check.ts` con un trabajo real | siempre |

## 2. Comprobaciones propias

1. Con un clip de 2 personas, transcribir con hablantes desde la app real. El resultado muestra dos nombres [AC-2, AC-4].
2. Renombrar, cerrar y reabrir desde la cola: el nombre sigue [AC-5].
3. Abrir `transcript.txt`: bloques con `[hh:mm:ss] Ana:` [AC-6].
4. Las capturas de claro y oscuro las revisa `image-reader`: el contraste de los colores de la paleta y los nombres visibles [AC-4].

Sin el motor instalado (falta el token): las pruebas 1 y 2 quedan en `PENDING/036-corrida-real`, y AC-3 se comprueba en real.

## 3. Escucha

No aplica.

## 4. Cierre, PR y merge

- [ ] `WARNING/036-seccion-transcripcion`.
- [ ] `docs/process/01-done/transcription.md` creada; `client.md` con la sección nueva en el Historial.
- [ ] Fases y fila del lote en `IMP`.
- [ ] `git fetch origin dev`, un push, PR, checks, `gh pr merge --merge` y `worktree close 036-transcription-section`.

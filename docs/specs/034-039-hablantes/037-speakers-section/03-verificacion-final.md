# Spec 037: verificación final

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación.
> Cada una queda anotada en [`docs/process/WARNING/`](../../../process/WARNING/README.md) (ficha `037-<tema>.md` con contexto, elegida, descartadas, cómo revertir y cómo comprobarla, y su fila en el README de la carpeta).
> Toda revisión pendiente queda en [`docs/process/PENDING/`](../../../process/PENDING/README.md) (ficha y fila, con qué la cierra).
>
> **Datos del usuario: solo los que crea esta spec**. La spec no borra ni sobrescribe voces grabadas (`server/data/narration/voz/`), voces construidas, salidas de `out/` ni modelos descargados que ella no creó. Sus pruebas escriben en carpetas nuevas (`out/<herramienta>/spec-037/` o `tmp/spec-037/`). Si algo parece exigir tocar datos existentes, no se decide al ejecutar: es un `blocked — user-data` y se pregunta. Los cambios locales o sin rastrear del checkout principal no son de la spec: no se tocan y no bloquean.

## 1. Batería

| # | Comando | Aplica si |
| :--- | :--- | :--- |
| 1 | `uv run ruff check && uv run ruff format --check` | siempre |
| 2 | `python -m devtools test-runner --type=all` | siempre |
| 3 | `python -m devtools test-runner --type=e2e` | siempre |
| 4 | `python -m devtools app-check run --scenario=speakers` y el smoke | siempre |
| 5 | Duración, LUFS y espectrograma de los WAV por hablante en `tmp/spec-037/`, revisados por `image-reader` | siempre |

## 2. Comprobaciones propias

1. En la app real, con el clip de 2 personas: las regiones coinciden con lo que se oye en 5 turnos elegidos al azar [AC-2].
2. Renombrar: `turns.csv` lleva el nombre nuevo [AC-3].
3. «Un audio por hablante» y escuchar los dos WAV [AC-5].
4. «Abrir en el Editor»: el proyecto abre con los marcadores y sus nombres [AC-6].

Sin el motor instalado: `PENDING/037-corrida-real` y se sigue.

## 3. Escucha

Las rutas de los WAV por hablante van al reporte y al PR.

## 4. Cierre, PR y merge

- [ ] `WARNING/037-seccion-hablantes`.
- [ ] `docs/process/01-done/diarization.md` actualizada.
- [ ] Fases y fila del lote en `IMP`.
- [ ] `git fetch origin dev`, un push, PR, checks, `gh pr merge --merge` y `worktree close 037-speakers-section`.

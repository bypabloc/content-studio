# Spec 034: verificación final

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación.
> Cada una queda anotada en [`docs/process/WARNING/`](../../../process/WARNING/README.md) (ficha `034-<tema>.md` con contexto, elegida, descartadas, cómo revertir y cómo comprobarla, y su fila en el README de la carpeta).
> Toda revisión pendiente queda en [`docs/process/PENDING/`](../../../process/PENDING/README.md) (ficha y fila, con qué la cierra).
>
> **Datos del usuario: solo los que crea esta spec**. La spec no borra ni sobrescribe voces grabadas (`server/data/narration/voz/`), voces construidas, salidas de `out/` ni modelos descargados que ella no creó. Sus pruebas escriben en carpetas nuevas (`out/<herramienta>/spec-034/` o `tmp/spec-034/`). Si algo parece exigir tocar datos existentes, no se decide al ejecutar: es un `blocked — user-data` y se pregunta. Los cambios locales o sin rastrear del checkout principal no son de la spec: no se tocan y no bloquean.

## 1. Batería

| # | Comando | Aplica si |
| :--- | :--- | :--- |
| 1 | `uv run ruff check && uv run ruff format --check` | siempre |
| 2 | `python -m devtools test-runner --type=all` | siempre |
| 3 | `uv run pytest -m local` | con el motor instalado (paso 2) |
| 4 | `python -m devtools test-runner --type=e2e` | siempre |
| 5 | `python -m devtools app-check run` (smoke) | siempre |

## 2. Comprobaciones propias

1. Si el usuario ya guardó su token, se instala `pyannote` desde la app o con `POST /engines/pyannote/install`. Se espera que:
   * `install.json` exista;
   * `models/community-1/config.yaml` esté presente;
   * `verify` importe `pyannote.audio` [AC-1, AC-2].

   Si el token falta, `PENDING/034-instalacion-real` (`blocked — user-credential`) y se sigue.
2. `rg -n "hf_" logs/jobs/<id>.log` y `install.json`: sin coincidencias [AC-2].
3. Con un token inválido de formato correcto: el trabajo termina con `engine_gated` y la tarjeta muestra el texto [AC-3].
4. Las capturas de app-check de Motores y Acerca de las revisa `image-reader` [AC-5, AC-6].

## 3. Escucha

No aplica.

## 4. Cierre, PR y merge

- [ ] Fichas `WARNING/034-token-en-settings` y `034-receta-pyannote`, y `PENDING` si aplica.
- [ ] `docs/process/01-done/engines.md` actualizada.
- [ ] Spec de lote: deja sus fases en `IMP` y su fila del lote en `IMP`; la carpeta la borra la 039.
- [ ] `git fetch origin dev` y merge de `origin/dev` si avanzó; un solo push.
- [ ] `gh pr create --base dev` si no existe; `gh pr checks <n> --watch`; `gh pr merge <n> --merge`.
- [ ] Desde el principal: `python -m devtools worktree close 034-diarization-engine`.

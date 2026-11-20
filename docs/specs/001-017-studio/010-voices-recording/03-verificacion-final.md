# 010: verificación final

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación. Cada una queda en [`docs/process/WARNING/`](../../../process/WARNING/README.md); toda revisión pendiente, en [`docs/process/PENDING/`](../../../process/PENDING/README.md).
>
> **Datos del usuario: solo los que crea esta spec**. No borra ni sobrescribe voces grabadas, voces construidas, salidas de `out/` ni modelos que no creó; si algo parece exigirlo, es un `blocked — user-data`. Excepción pedida: `move-data` mueve las referencias actuales al perfil `default`.

## 1. Batería

1. `python -m devtools test-runner --type=all`, `--type=e2e`, `--type=tauri-check` y `--type=guard-tdd`.
2. `python -m devtools spelling`, sin exclusiones temporales en `cspell.config.yaml` (AC-10).
3. `uv run pytest -m local`.
4. `uv run studio narration voices --list | cat` y `uv run studio narration tts --help | cat` (aparece `--profile`).

## 2. Migración y corridas reales (en el principal, justo antes del merge para la migración)

1. Anota la cantidad y los bytes de `reference/**`. Corre `move-data` (plan) y después `--apply`. Comprueba que todo esté en `reference/default/` (AC-1).
2. Con el turno: `uv run studio narration tts --model voxcpm2 --profile default --style expert --text "Prueba de la spec siete."` (si `default` tiene `expert`; si no, una voz del catálogo para comparar). Compara la duración y los LUFS con una narración equivalente de antes (AC-11).
3. App en `tauri dev`, con el perfil nuevo «Spec 010»:
   * Prueba de sala y graba `neutral` con el micrófono real del equipo. La toma se sube, el chequeo corre y aparece el veredicto.
   * `ffprobe` de la toma: 48000 Hz, 1 canal y `s32` o `s24` (AC-3 real). Saca el espectrograma en `tmp/spec-010/take.png`, que revisa `image-reader`: sin el recorte de banda de opus (energía por encima de 16 kHz si el micrófono la capta) ni las compuertas de un noise gate.
   * Importa un tramo de 10 s de un video de `tmp/spec-010/` con la casilla de permiso. Sin la casilla, la UI no deja confirmar.
   * Construye una voz del catálogo que todavía no esté construida (si las 15 están construidas, `Forzar` sobre una) y comprueba el progreso en la cola.
   * Marca una favorita y comprueba el orden en Narración.
4. Borra el perfil «Spec 010»: queda en `.trash/` y no se pierde ningún byte. La papelera de prueba se puede borrar porque es dato de la spec.
5. Capturas de las tres pantallas en claro y en oscuro en `tmp/spec-010/`, que revisa `image-reader`.

## 3. Escucha

Las rutas de la toma grabada, el tramo importado y la narración con `--profile default` van en el reporte.

## 4. Cierre

* `docs/process/01-done/`, con la ficha `voices.md` o la actualización de `narration.md`.
* Fichas WARNING `010-captura-pcm.md` y `010-permiso-microfono-webview2.md`, y PENDING `010-whisper-a-faster-whisper.md`. Se borra `PENDING/002-cspell-excepciones-temporales.md` y su fila.
* Estado de la fila 010 en el README del lote.

## 5. PR y merge

1. `git fetch origin dev` y merge si avanzó; un solo push.
2. PR a `dev` si no existe, con capturas, los pasos de `move-data` y las fichas.
3. `gh pr checks <n> --watch` y `gh pr merge <n> --merge`.
4. En el principal: `git switch dev && git pull`, `uv sync` (sale el grupo `legacy`) y `python -m devtools worktree close 010-voices-recording`.

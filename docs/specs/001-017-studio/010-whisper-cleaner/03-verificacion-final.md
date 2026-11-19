# 010: verificación final

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación. Cada una queda en [`docs/process/WARNING/`](../../../process/WARNING/README.md); toda revisión pendiente, en [`docs/process/PENDING/`](../../../process/PENDING/README.md).
>
> **Datos del usuario: solo los que crea esta spec**. No borra ni sobrescribe voces grabadas, voces construidas, salidas de `out/` ni modelos que no creó; si algo parece exigirlo, es un `blocked — user-data`. El archivo de entrada nunca se modifica.

## 1. Batería

1. `python -m devtools test-runner --type=all`, `--type=e2e`, `--type=budget` y `--type=guard-tdd`.
2. `uv run pytest -m local` (incluye la transcripción de 3 s con `small` y el render con NVENC).
3. `uv run studio clean --help | cat` y `uv run studio clean tmp/spec-010/no-existe.mp4`, que tiene que salir con exit 2 y un mensaje del catálogo.

## 2. Corridas reales (con el turno para la transcripción)

1. Instala faster-whisper desde Motores y descarga large-v3-turbo (en segundo plano, con el log en `logs/engines-install-whisper-spec-010.log`).
2. **Video real**: el usuario aporta uno de 3 a 5 minutos (o se graba uno de prueba con la cámara y el micrófono del equipo, guardado en `tmp/spec-010/`). Analiza, revisa en la UI (desactiva un corte, arrastra el borde de otro y cambia el hueco a 700 ms) y renderiza.
3. Mediciones de la salida (AC-11):
   * Duración antes y después, que tiene que coincidir con `report.json`.
   * `silencedetect=n=-50dB:d=0.8` sobre el audio del limpio: ningún hueco de más de 0,8 s.
   * Sincronía: el audio y el video del limpio duran lo mismo ± 1 cuadro (`ffprobe` por stream).
   * VRAM pico de la transcripción (`nvidia-smi --query-gpu=memory.used` muestreado durante el trabajo), menor que 3 GB.
   * Espectrograma del audio limpio en `tmp/spec-010/clean.png`, que revisa `image-reader`: sin clics (líneas verticales de banda ancha) en los cortes.
4. **Audio solo**: una narración de la 006 con silencios largos agregados a mano (con ffmpeg en `tmp/spec-010/`). Limpia y mide igual.
5. **Lote**: tres archivos con «Aplicar todos sin revisar».
6. **Exportaciones**: importa `cuts.xml` en DaVinci Resolve si está instalado, o abre `cuts.edl` y valida su formato con el test. Anota en WARNING si no se pudo probar en un editor real.
7. **Evaluación migrada**: `uv run studio narration tts --evaluate ...` con el turno, y que use faster-whisper (AC-10).
8. Capturas de la revisión con video y con solo audio, en claro y en oscuro, en `tmp/spec-010/`, que revisa `image-reader`.

## 3. Escucha

Las rutas del video limpio, el audio limpio y su SRT van en el reporte. El usuario decide si los cortes suenan naturales. Si pide otros valores por defecto (hueco o margen), se cambian en esta spec, porque son dos números.

## 4. Cierre

* `docs/process/01-done/cleaner.md`, nueva, y `narration.md` con la evaluación nueva.
* Fichas WARNING `010-cuda-windows.md` y `010-render-precision.md`. Se borra `PENDING/007-whisper-a-faster-whisper.md` y su fila.
* Estado de la fila 010 en el README del lote.

## 5. PR y merge

1. `git fetch origin dev` y merge si avanzó; un solo push.
2. PR a `dev` si no existe, con las mediciones, las capturas, las rutas para escuchar y ver, y las fichas.
3. `gh pr checks <n> --watch` y `gh pr merge <n> --merge`.
4. En el principal: `git switch dev && git pull` y `python -m devtools worktree close 010-whisper-cleaner`.

# 009: verificación final

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación. Cada una queda en [`docs/process/WARNING/`](../../../process/WARNING/README.md); toda revisión pendiente, en [`docs/process/PENDING/`](../../../process/PENDING/README.md).
>
> **Datos del usuario: solo los que crea esta spec**. No borra ni sobrescribe voces grabadas, voces construidas, salidas de `out/` ni modelos que no creó; si algo parece exigirlo, es un `blocked — user-data`. Los motores `external` del equipo no se tocan.

## 1. Batería

1. `python -m devtools test-runner --type=all`, `--type=e2e`, `--type=tauri-check` y `--type=guard-tdd`.
2. `uv run pytest -m local`: los motores actuales (`external`) siguen funcionando con las rutas dinámicas.
3. `uv run studio engines list | cat` (los motores del equipo aparecen como `external`), `uv run studio engines install foo` (exit 2) y `uv run studio engines uninstall voxcpm2` (exit 1, `engine_external`, sin borrar nada).

## 2. Corridas reales

1. **Instalación real en una carpeta temporal** (AC-10): en la app (`tauri dev`), en Ajustes > Almacenamiento, apunta `storage.engines` a `tmp/spec-009/data/`. Instala Qwen 0.6B desde Motores, en segundo plano, con el log en `logs/engines-install-qwen-spec-009.log`. Comprueba el progreso por paso y por bytes. Corta la red o cancela a la mitad de la descarga y reintenta: sigue desde el paso `hf` y retoma el parcial.
2. Verifica (con el turno de GPU): genera 1 s. Mide la duración del archivo de prueba con `ffprobe`.
3. Repara: no vuelve a descargar los pesos (el tamaño descargado es cero y el tiempo, corto).
4. Desinstala: `tmp/spec-009/data/` queda vacía. Vuelve `storage.engines` al valor por defecto y comprueba que los motores `external` siguen `installed` y la narración funciona.
5. **ffmpeg**: con el PATH de la sesión de prueba sin ffmpeg (sin desinstalar el del sistema), `GET /system` dice que falta y aparece el banner. «Instalar ffmpeg» corre winget. Si el ffmpeg del sistema ya está instalado por winget, winget informa que ya existe y la app lo detecta. Anota el resultado real en WARNING `009-winget.md`.
6. **Mover salidas entre discos**: si el equipo tiene un segundo volumen (C: y D:), mueve `storage.outputs` a una carpeta de prueba en el otro volumen con 2 o 3 salidas de prueba (creadas por esta spec), comprueba los sha256 y que `/files` sirve las rutas antiguas. Después vuelve a moverla. Si no hay segundo volumen, queda cubierto por AC-7 y se anota.
7. **Bienvenida**: con una base nueva (`var/` temporal, `CONTENT_STUDIO_DB=tmp/spec-009/db.sqlite`), sin `storage` y con `CONTENT_STUDIO_MODE=installed` apuntando a carpetas temporales. Aparece la bienvenida, se recorren los 4 pasos sin instalar nada pesado (desmarcando el paquete) y no vuelve a salir.
8. Capturas de Motores, Almacenamiento y Bienvenida en claro y en oscuro en `tmp/spec-009/`, que revisa `image-reader`.

## 3. Cierre

* `docs/process/01-done/engines.md`, nueva.
* Fichas WARNING `009-recetas.md`, `009-winget.md` y `009-mover-entre-discos.md`.
* Se borra `tmp/spec-009/` (datos de la spec).
* Estado de la fila 009 en el README del lote.

## 4. PR y merge

1. `git fetch origin dev` y merge si avanzó; un solo push.
2. PR a `dev` si no existe, con las capturas, el resultado de la instalación real (tiempos y tamaños) y las fichas.
3. `gh pr checks <n> --watch` y `gh pr merge <n> --merge`.
4. En el principal: `git switch dev && git pull` y `python -m devtools worktree close 009-engines-storage`.

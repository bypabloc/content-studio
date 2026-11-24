# Instalación, Privacidad y Almacenamiento

> Investigación del 2026-11-15. Cómo instalar VoiceStudio en Linux, WSL2 y Docker con NVIDIA si se quisiera usar la app, qué datos guarda y dónde, qué sale a la red y cómo se comparte, se actualiza o se usa desde el móvil. Índice en [README.md](README.md). Marcas: **(leída)**, **(snippet)**, **no verificado**, **conflicto**; comunidad A/B/C ([01](../01-metodo-y-fuentes.md) §3).

---

## 1. Qué Es

| Vía | Para qué | Interfaz | Fuente |
| :--- | :--- | :--- | :--- |
| **AppImage / .deb / Snap** | Escritorio Linux x86_64 (X11 o Wayland) | Electron | `docs/install/linux.md` **(leída)** |
| **Docker** (`ghcr.io/debpalash/voicestudio`) | Servidor sin pantalla; UI en el navegador | Web en `:3900` | `docs/install/docker.md` **(leída)** |
| **Código fuente** (`bun` + `uv`) | Desarrollo | Electron con recarga en caliente | `linux.md` §Building from source **(leída)** |
| **Python existente** | Usar un venv propio en vez del runtime gestionado | — | `docs/existing-python-runtime.md` **(leída)** |
| **Móvil** (iOS 17+, Android 10+) | Generación en el teléfono o emparejado con el PC. **Preview**: fuera de las tiendas | App nativa | `docs/mobile.md` **(leída)** |

**Local-first:** el backend escucha solo en `127.0.0.1`; compartir en red y usar un backend remoto son opciones que se activan a mano (`docs/sharing.md` L3) **(leída)**.

---

## 2. Cómo Se Usa

### 2.1 Linux nativo (AppImage)

```bash
curl -fsSL https://voicestudio.sh/install | sh      # baja la AppImage y verifica SHA256SUMS.txt
# o a mano:
chmod +x VoiceStudio-*-linux-x64.AppImage && ./VoiceStudio-*-linux-x64.AppImage
```

Requisitos: **~10 GB libres**, driver NVIDIA opcional. En el primer arranque la app instala Python, FFmpeg, yt-dlp y el torch CUDA (~3 GB de paquetes `nvidia-*`). Sin NVIDIA instala torch CPU y necesita ~5 GiB. `OMNIVOICE_TORCH_VARIANT=cuda|cpu|rocm` fuerza la variante **(leída, `linux.md` L7-20, L95-107)**.

### 2.2 WSL2 con NVIDIA

Ninguna guía cubre **WSL2 + NVIDIA** para la app de escritorio. WSL2 aparece solo para AMD/ROCm (`wsl-amd-rocm.md`, `docker.md` §AMD GPU on WSL2) y como forma de esquivar Smart App Control de Windows (`troubleshooting.md` L1580) **(leída)**. Opciones razonables, todas **no verificado**:

| Opción | Cómo | Riesgo |
| :--- | :--- | :--- |
| **A. Docker dentro de WSL2** (la más limpia) | `docker compose --profile gpu`, con NVIDIA Container Toolkit en WSL. Probar antes con `docker run --rm --gpus all nvidia/cuda:12.8.0-base-ubuntu22.04 nvidia-smi` (`docker.md` §Troubleshooting) | La UI en Docker oculta los controles nativos (selector de carpetas, carpetas locales de modelos) |
| **B. AppImage en WSLg** | Ejecutar la AppImage en la distro; WSLg muestra la ventana | Electron en WSLg con GPU: si la ventana queda en blanco, `--disable-gpu` (`linux.md` L274-284) |
| **C. Backend en WSL2 y app en Windows** | Backend desde el código con `OMNIVOICE_API_KEY` y la app de Windows en *Remote backend* ([14](14-modelos-y-hardware.md) §2.5) | Más piezas; la IP de WSL cambia |

### 2.3 Docker con NVIDIA

```bash
export OMNIVOICE_API_KEY="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
docker run -d --name omnivoice --gpus all \
  -p 127.0.0.1:3900:3900 \
  -e OMNIVOICE_API_KEY="$OMNIVOICE_API_KEY" \
  -e OMNIVOICE_DATA_DIR=/app/omnivoice_data \
  -v omnivoice-data:/app/omnivoice_data \
  ghcr.io/debpalash/voicestudio:stable
# o: docker compose -f deploy/docker-compose.yml --profile gpu up -d
```

Abrir `http://localhost:3900`; el primer arranque baja ~2,4 GB. La API key es obligatoria porque el NAT de Docker impide demostrar que el navegador es el host. Usar `:stable` y no `:latest`, que sigue `main` **(leída, `docker.md` L43-125, L322-340)**.

**Reutilizar la caché de HF del host** (para no bajar otra vez lo que `narration/` ya tiene):

```bash
-v ~/.cache/huggingface:/app/omnivoice_data/huggingface
```

Montar en `/root/.cache/huggingface` no tiene efecto, porque la imagen fija `HF_HOME`. El contenedor corre como root y deja archivos de root en el host **(leída, `docker.md` §Volume mounts)**.

### 2.4 Usar un Python propio

Settings → Performance → *Python runtime* → *Choose interpreter* (por ejemplo `.venv/bin/python`). La app valida con imports reales de FastAPI, Uvicorn, OmniVoice, Torch y los motores, y no instala nada sin una confirmación doble. Exige Python ≥3.11; rechaza 3.10. `OMNIVOICE_BACKEND_CMD` tiene prioridad sobre la selección **(leída, `existing-python-runtime.md`)**.

---

## 3. Opciones y Parámetros

### 3.1 Dónde guarda cada cosa (Linux AppImage/.deb)

| Ruta | Contenido | Fuente |
| :--- | :--- | :--- |
| `~/.omnivoice/` | **Datos**: voces, proyectos, `omnivoice.db`, salidas generadas, `omnivoice.log`, *sidecars*, `prompt_cache/` | `docs/install/uninstall.md` L141-147 **(leída)** |
| `~/.config/VoiceStudio/` | Carpeta de la app, logs del escritorio y **runtime Python gestionado** (`runtime/project/.venv`, varios GB) | **(leída)** |
| `~/.config/omnivoice/` | Archivo `env`: ubicación de caché, token HF (cifrado), elección de ROCm; también las variables de [14](14-modelos-y-hardware.md) §3 | **(leída)**; token cifrado con Fernet + scrypt (`pyproject.toml`, AUTH-02) |
| `~/.cache/huggingface/` | **Pesos de modelos**: caché HF **compartida** con otras herramientas | **(leída)** |
| `~/.cache/voicestudio-electron-updater/` | Actualizaciones descargadas | **(leída)** |
| `~/.cache/audioseal/` | Checkpoint de la marca de agua ([13](13-marca-de-agua.md)) | `watermark.py` L285-294 **(leída)** |
| Docker: volumen `omnivoice-data` → `/app/omnivoice_data` | Todo: BD, voces, ajustes, token HF y caché HF | `docker.md` §Volume mounts **(leída)** |

Variables para moverlo: `OMNIVOICE_DATA_DIR`, `OMNIVOICE_CACHE_DIR`, `HF_HOME`, `HF_HUB_CACHE` **(leída, `uninstall.md` L182)**.

### 3.2 Qué sale a la red

| Tráfico | Default | Control | Fuente |
| :--- | :--- | :--- | :--- |
| Descarga de modelos (HF o `hf-mirror.com`) | Al instalar o usar un motor | `HF_ENDPOINT`, carpetas locales | `downloading-models.md` **(leída)** |
| Analítica de uso (Supermetry) | **Apagada** hasta consentir; solo etiquetas fijas de pantallas y acciones, sin texto, audio, rutas ni mensajes | Settings → Privacy; `OMNIVOICE_ANALYTICS_DISABLED=1` en Docker | `electron-privacy.md` L27-29; `docker.md` L8-12 **(leída)** |
| Reportes de error automáticos | **Apagados**, con consentimiento propio; solo categorías y códigos | Settings → Privacy | `electron-privacy.md` §Automatic error reports **(leída)** |
| Buscar actualizaciones | ~10 s tras abrir y cada 6 h; descarga automática **activada** por defecto, instalación nunca forzada | Settings → Updates | `docs/update-channels.md` **(leída)** |
| Checkpoint de AudioSeal | Solo si no está en caché y al marcar | `OMNIVOICE_PRELOAD_WATERMARK` | [13](13-marca-de-agua.md) |
| VoiceStudio Cloud (cuenta) | Apagado hasta iniciar sesión | — | `electron-privacy.md` L31-38 **(leída)** |

### 3.3 Retención y borrado

* **Historial:** límite configurable (0 = ilimitado, hasta 100 000). La limpieza borra tomas viejas sin estrella y su audio; bajar el límite pide confirmación **(leída, `electron-privacy.md` L196)**.
* **Settings → Storage:** uso por categoría (modelos, datos, entornos de motores, temporales), mover la carpeta de datos (copia, verifica y luego borra el original) y *Reset & remove* por alcance, con confirmación escrita para voces y proyectos **(leída, `electron-storage.md`)**.
* **Paquete de diagnóstico** (Settings → About): `render_traces.json` con los últimos 32 renders. No incluye guiones, nombres de voz, rutas ni audio, y no se sube solo **(leída, `performance.md` L426-438)**.

---

## 4. Ejemplos

| Caso | Comando o paso |
| :--- | :--- |
| Ver la versión en Docker | `curl http://127.0.0.1:3900/health` → `{"status":"ok","device":"cuda (...)","version":...}` |
| Ver el progreso del arranque | `GET /startup/progress` (mientras `/health` da 503) |
| Abrir la UI de Docker desde el móvil en la LAN | Pie de página → **Local** → **Network** → escanear el QR + PIN (`sharing.md`) |
| Bloquear la analítica en Docker | `-e OMNIVOICE_ANALYTICS_DISABLED=1` |
| Canal beta | Settings → Updates → *Update channel* → Beta (no hay degradación al volver a Stable) |
| Desinstalar sin perder pesos de otras herramientas | Borrar `~/.omnivoice`, `~/.config/VoiceStudio`, `~/.config/omnivoice` y **no** `~/.cache/huggingface` |

---

## 5. Tips y Trucos

* **La caché de HF es compartida.** VoiceStudio usa `~/.cache/huggingface` por defecto, la misma que pueden usar los venvs de `narration/`. Borrar "modelos" desde la app puede llevarse pesos que usa otra herramienta: la app lo advierte, pero conviene saberlo **(leída, `electron-storage.md`; `uninstall.md`)**.
* **Verificar cada descarga** contra `SHA256SUMS.txt` del release **(leída, `linux.md` L94)**.
* **Docker solo en loopback:** mantener `-p 127.0.0.1:3900:3900`. Para acceso remoto, Tailscale Serve, nunca Funnel **(leída, `docker.md`, `remote-gpu.md`)**.
* **Escribir con la caché de HF del host montada** deja archivos de root; corregir con `sudo chown -R $USER ~/.cache/huggingface` después.
* **Electron en blanco o con errores de GPU** (frecuente en entornos virtuales): `./VoiceStudio-*.AppImage --disable-gpu` **(leída, `linux.md` L274-284)**.

---

## 6. Problemas Conocidos

| Problema | Estado | Fuente |
| :--- | :--- | :--- |
| `403 loopback origin required` en Docker sobre WSL: toda la configuración bloqueada | Cerrado; la imagen trae `OMNIVOICE_SERVER_MODE=1` | [#1651](https://github.com/debpalash/VoiceStudio/issues/1651) **(leída)**; `docker.md` §Troubleshooting |
| No reconoce la GPU AMD 7900XTX en Docker WSL | Cerrado | [#1655](https://github.com/debpalash/VoiceStudio/issues/1655) (título) **(snippet)** |
| Docker: el navegador del propio host recibe la puerta del PIN y el PIN no se recupera | Cerrado | [#3003](https://github.com/debpalash/VoiceStudio/issues/3003) (título) **(snippet)** |
| Falta `cudnn8_compat` en la imagen Docker | Cerrado | [#2050](https://github.com/debpalash/VoiceStudio/issues/2050) (título) **(snippet)** |
| La ruta del MP3 de audiolibro da 404 | Cerrado 2026-11-13 | [#4071](https://github.com/debpalash/VoiceStudio/issues/4071) (título) **(snippet)** |
| Windows bloquea `python.exe` sin firmar (Smart App Control) | Abierto | [#3635](https://github.com/debpalash/VoiceStudio/issues/3635) (título) **(snippet)** |
| **conflicto:** el destino de los reportes de error figura "fijado por el dueño 2026-11-16", un día después de la fecha de esta investigación | Probable error de fecha en la doc | `electron-privacy.md` §Automatic error reports **(leída)** |
| **conflicto (licencia del proyecto):** `pyproject.toml` dice AGPL-3.0-only con licencia comercial aparte; Tessl lista FSL-1.1-ALv2 | Prevalece el repo | `pyproject.toml` L14 **(leída)**; [tessl.io](https://tessl.io/registry/skills/github/debpalash/OmniVoice-Studio/omnivoice) **(snippet, C)** |

---

## 7. Qué Dice la Comunidad

* Las reseñas la presentan como una alternativa local a ElevenLabs, sin cuenta ni API key ([andrew.ooo](https://andrew.ooo/posts/voicestudio-review-local-elevenlabs-alternative/), [pyshine](https://pyshine.com/voicestudio-open-source-local-voice-cloning-dubbing/)) **(snippet, C)**.
* Otras más críticas la ven como "más experimento que herramienta de producción" ([KaiAI](https://kai.nguyenphivan.com/tools/omnivoice-studio)) y dicen que "la voz local aún tiene que probarse" ([remio](https://www.remio.ai/post/debpalash-voicestudio-hit-github-trending-but-local-voice-ai-still-has-to-prove)) **(snippet, C)**.
* Un fork o guía de Docker advierte que una versión antigua no tenía autenticación ([gmossy/omnivoice-studio](https://github.com/gmossy/omnivoice-studio)) **(snippet, C)**. Las versiones actuales exigen `OMNIVOICE_API_KEY` en Docker: el dato está desactualizado.
* Hay guías de instalación de terceros ([computingforgeeks](https://computingforgeeks.com/install-voicestudio/), [KDnuggets](https://kdnuggets.com/getting-started-with-omnivoice-studio)) **(snippet, C)**. No se leyeron en detalle.

---

## 8. Qué Sirve para social-videos

1. **No hace falta instalar la app** para lo que hace `narration/`: los motores se integran directo ([02](../02-voicestudio.md)). Si se quiere probarla como referencia, la vía menos invasiva es **Docker dentro de WSL2** con `--gpus all`, en loopback, montando `~/.cache/huggingface` para no bajar otra vez OmniVoice ni VoxCPM2. **No verificado** en esta máquina.
2. **Espacio:** el runtime gestionado (varios GB en `~/.config/VoiceStudio`) más el torch CUDA (~3 GB) más los modelos. Con 627 GB libres en `/` (medido con `df`) no es un problema; sí lo sería la duplicación de torch si se agregan *sidecars*.
3. **Una GPU, un proceso.** Con VoiceStudio abierto (OmniVoice residente 15 min por `OMNIVOICE_IDLE_TIMEOUT_S`) y `narration/tts.py` corriendo a la vez se rompe la regla 2 de `AGENTS.md`. Hay que cerrar la app o usar `POST /model/unload/tts` antes.
4. **Privacidad aceptable para voces propias:** todo es local por defecto, la analítica y los reportes son opt-in y el token HF va cifrado. La voz clonada (`~/.omnivoice/`) queda en disco sin cifrar **no verificado**; tratarla como dato personal (no subirla a repos, respetar el `.gitignore` de `out/` y `logs/`).
5. **Ideas para copiar:** el paquete de diagnóstico sin contenido (solo tiempos por etapa) es un buen modelo para los `logs/` de este repo, donde hoy no conviene guardar textos de guion en logs compartibles. También la separación datos / runtime / caché de modelos con variables `*_DIR` sobreescribibles.

# Spec 034: contexto y decisión

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación.
> Cada una queda anotada en [`docs/process/WARNING/`](../../../process/WARNING/README.md) (ficha `034-<tema>.md` con contexto, elegida, descartadas, cómo revertir y cómo comprobarla, y su fila en el README de la carpeta).
> Toda revisión pendiente queda en [`docs/process/PENDING/`](../../../process/PENDING/README.md) (ficha y fila, con qué la cierra).
>
> **Datos del usuario: solo los que crea esta spec**. La spec no borra ni sobrescribe voces grabadas (`server/data/narration/voz/`), voces construidas, salidas de `out/` ni modelos descargados que ella no creó. Sus pruebas escriben en carpetas nuevas (`out/<herramienta>/spec-034/` o `tmp/spec-034/`). Si algo parece exigir tocar datos existentes, no se decide al ejecutar: es un `blocked — user-data` y se pregunta. Los cambios locales o sin rastrear del checkout principal no son de la spec: no se tocan y no bloquean.

## 1. Precondición

No depende de otra spec. Antes del primer commit:

```bash
git cat-file -e origin/dev:server/src/content_studio/engines/recipes.py || echo FALLA
git cat-file -e origin/dev:docs/research/diarizacion-pyannote/README.md || echo FALLA
```

Si la 026 ya está en `origin/dev`, primero la fase `0-ajustes` del [README del lote](../README.md).

## 2. Contexto

La transcripción con faster-whisper ya funciona, pero nada dice quién habla. La investigación eligió pyannote 4.x con community-1. Sus pesos están en un repositorio **restringido** de Hugging Face: hay que aceptar condiciones y usar un token. Hoy la app no tiene dónde guardar un token, y el paso de instalación `hf` descarga sin autenticarse.

### Términos

| Término | Significado | En el código |
| :--- | :--- | :--- |
| Diarización | Dividir un audio en turnos por hablante | familia `diarization` |
| Repositorio restringido (*gated*) | Repositorio de Hugging Face que exige aceptar condiciones y un token | `"gated": true` en el paso `hf` |
| Token de Hugging Face | Credencial de lectura del usuario (`hf_…`) | `secret.huggingface.token` |

### Hallazgos de la exploración

- **El paso `hf` descarga sin token.** `server/src/content_studio/engines/steps.py` (`_download`) llama a `HfApi().model_info` y `snapshot_download` sin `token=`. `HF_HOME` apunta a la caché del motor, así que un `token` guardado por `huggingface-cli` tampoco se usaría.
- **Un repositorio restringido falla sin un código propio.** `model_info` lanza `GatedRepoError` (401 o 403) y el paso termina en un `CalledProcessError` genérico. `installer.EXIT_CODES` solo tiene del 20 al 24.
- **La receta no admite campos nuevos.** `recipes.OPTIONAL['hf']` solo acepta `allow_patterns` e `ignore_patterns`, y cualquier otro campo da `ValueError`. `recipes.FAMILIES` no incluye `diarization`. `PYTHON` admite de 3.10 a 3.12.
- **No hay almacén de credenciales.** `api/routes/settings.py` (`read_setting`) devuelve cualquier clave, y `write_setting` solo bloquea `storage.*`. No existe `HF_TOKEN` en `server/src` ni en `client/src`.
- **Motores no muestra familias nuevas.** `client/src/features/engines/EnginesPage.tsx` (`GROUPS`) lista narración, música, transcripción y asistente.
- **El repositorio de pesos** (medido el 2026-11-24 con la API pública de Hugging Face):
  * SHA `3533c8cf8e369892e6b79ff1bf80f7b0286a54ee`, con `gated: auto` (la aprobación es automática al aceptar);
  * archivos: `config.yaml`, `segmentation/pytorch_model.bin`, `embedding/pytorch_model.bin` y `plda/{plda,xvec_transform}.npz`.
- **Versiones** ([investigación 02](../../../research/diarizacion-pyannote/02-versiones-e-instalacion.md)): pyannote 4.1.1 pide Python ≥ 3.11 y torchcodec 0.17 pide torch ≥ 2.11.

## 3. Solución

* Una receta `pyannote.json` con la familia `diarization` y un paso `hf` con `"gated": true`.
* El instalador pasa el token por `HF_TOKEN` a ese paso y traduce el 401 o 403 de Hugging Face en `engine_gated`.
* Rutas `/credentials/huggingface` para guardar, consultar y borrar el token. La consulta solo dice si hay uno configurado, nunca su valor.
* En Motores, la tarjeta «Diarización (pyannote)»:
  * un campo para el token;
  * un enlace para aceptar las condiciones;
  * la licencia CC-BY-4.0 con su atribución.

Decisiones:

- **D-1: token del usuario** — lo eligió el usuario. Se descarta el espejo propio porque las condiciones completas del repositorio no se leyeron, y la [investigación 07](../../../research/diarizacion-pyannote/07-licencias-privacidad-y-seguridad.md) lo deja como opción B.
- **D-2: `settings` con la clave `secret.*` bloqueada en la API genérica** — ya existe y es local. Se descarta el llavero del sistema (`keyring` o Tauri) porque sería una dependencia nueva. Se descarta el archivo `$HF_HOME/token` porque viviría dentro de la carpeta de motores, que se mueve y se comparte entre worktrees.
- **D-3: `HF_TOKEN` en el entorno del paso** — `huggingface_hub` ya lo lee. Se descartan `argv` y el JSON del paso, porque se verían en la lista de procesos y en el log.
- **D-4: `engine_token_required` y `engine_gated`** — el usuario debe saber qué hacer. Se descarta el error genérico de hoy.
- **D-5: versiones de la receta** — la 4.1.1 trae los arreglos de VBx y del DER, y torch 2.11 con cu128 ya funciona en este equipo con Qwen. Se descarta 4.0.7 con Python 3.10, que no trae esos arreglos.
- **D-6: familia `diarization` propia** — es un producto distinto de `transcription` y tiene su venv. Se descarta meterlo en `transcription`, porque ese grupo muestra los modelos de Whisper.

## 4. Fuera de alcance

- Ejecutar la diarización, el servicio y la verificación de humo de la familia: es la 035.
- Un espejo de los pesos o un instalador que los incluya (investigación 07, opción B).
- Cifrar el token en reposo; queda en la ficha `WARNING/034-token-en-settings`.
- Otros motores restringidos: el mecanismo sirve para ellos, pero esta spec solo agrega `pyannote`.

## 5. Criterios de aceptación

- **AC-1**: WHEN se carga `recipes.load('pyannote')` THEN:
  * la familia es `diarization` y Python es 3.12;
  * torch, torchaudio, pyannote.audio, torchcodec y huggingface-hub están fijados con `==`;
  * el paso `hf` trae el repositorio, la revisión de 40 caracteres, `"gated": true` y `into: models/community-1`;
  * la receta termina en `verify` con `import pyannote.audio`.
- **AC-2**: Given un token guardado When corre el paso `hf` restringido Then el proceso hijo recibe `HF_TOKEN` en su entorno, y el token no aparece en `argv`, el log del trabajo ni `install.json`.
- **AC-3**: Hay dos casos de error:
  * WHEN se pide instalar `pyannote` sin token THEN `POST /engines/pyannote/install` responde 409 con `error.engine_token_required`, sin encolar;
  * WHEN Hugging Face responde 401 o 403 THEN el paso sale con 25 y el trabajo termina con `error.engine_gated`.
- **AC-4**: WHEN se llama a `PUT /credentials/huggingface` con un token THEN `GET /credentials/huggingface` devuelve `{"configured": true}` sin el valor. `GET` y `PUT` de `/settings/secret.huggingface.token` responden 403. `DELETE` deja `configured: false`. Un token que no empieza con `hf_` responde 422.
- **AC-5**: WHEN el usuario abre Motores THEN ve el grupo «Diarización» con la tarjeta del motor. Sin token, la tarjeta muestra:
  * el campo del token;
  * el enlace para aceptar las condiciones;
  * «Instalar» deshabilitado.

  Con el token guardado, el campo dice «Token guardado» con la opción «Quitar», e «Instalar» se habilita.
- **AC-6**: WHEN el usuario abre Ajustes > Acerca de THEN ve la atribución de community-1 (CC-BY-4.0, con enlace) y la licencia MIT de pyannote.audio.

## 6. Debe sonar / no debe sonar

No aplica: esta spec no genera audio.

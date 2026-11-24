# Spec 026: contexto y decisión

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación.
> Cada una queda anotada en [`docs/process/WARNING/`](../../../process/WARNING/README.md) (ficha `026-<tema>.md` con contexto, elegida, descartadas, cómo revertir y cómo comprobarla, y su fila en el README de la carpeta).
> Toda revisión pendiente queda en [`docs/process/PENDING/`](../../../process/PENDING/README.md) (ficha y fila, con qué la cierra).
>
> **Datos del usuario: solo los que crea esta spec**. La spec no borra ni sobrescribe voces grabadas (`server/data/narration/voz/`), voces construidas, salidas de `out/` ni modelos descargados que ella no creó. Sus pruebas escriben en carpetas nuevas (`out/<herramienta>/spec-026/` o `tmp/spec-026/`). Si algo parece exigir tocar datos existentes, no se decide al ejecutar: es un `blocked — user-data` y se pregunta. Los cambios locales o sin rastrear del checkout principal no son de la spec: no se tocan y no bloquean.

## 1. Precondición

```bash
git fetch origin dev
git log origin/dev --merges --oneline | grep -q 'chore/025-server-python' || echo FALLA
git cat-file -e origin/dev:.python-version || echo FALLA
git cat-file -e origin/dev:devtools/python_floor.py || echo FALLA
python -m devtools gpu-turn status   # la GPU libre antes de cada corrida
```

## 2. Contexto

Cada motor vive en su venv, creado por su receta (`server/src/content_studio/engines/recipes/<motor>.json`) con una Python, torch, paquetes, commits de git y revisiones de Hugging Face fijados. Hoy CosyVoice 3 y HeartMuLa usan 3.10, IndexTTS 3.11 y los demás 3.12; torch va de 2.10 a 2.11 con CUDA 12.8; `huggingface-hub` está en 0.36.2 en casi todas. El código de `content_studio` corre dentro de esos venvs, así que el más viejo fija la sintaxis de todo lo compartido (spec 025).

### Términos

| Término | Significado | En el código |
| :--- | :--- | :--- |
| Receta | JSON con los pasos de instalación de un motor | `server/src/content_studio/engines/recipes/*.json`, `engines/recipes.py` |
| Huella | sha256 del JSON de la receta instalada | D-2 |
| `outdated` | Estado de un motor instalado cuya receta cambió | `/engines` (D-2) |
| Carpeta aislada | `storage.engines` apuntando a `tmp/spec-026/engines` | D-3 |

### Hallazgos de la exploración

- **14 recetas** (medido el 2026-11-24): narración `voxcpm2`, `qwen-0.6b`, `qwen-1.7b`, `chatterbox`, `cosyvoice3`, `omnivoice`, `indextts`; música `acestep`, `heartmula`; `faster-whisper`, `vision`, y el asistente `llama-cpp` (zip `b12676`, CUDA 12.4), `gemma-4-e4b` y `qwen3.5-9b` (GGUF).
- **Python por receta**: 3.10 `cosyvoice3`, `heartmula`; 3.11 `indextts`; 3.12 el resto.
- **torch 2.15.0** publica wheels cp311–cp315 (PyPI, 2026-11-24); las recetas usan 2.10.0 y 2.11.0 `+cu128`.
- **Sin detección de cambios**: `engines/installer.py` y `engines/verification.py` comprueban imports y archivos, no si la receta instalada es la vigente.
- **Los pasos `hf` guardan la revisión** en un archivo de referencia (`steps.py`, paso `hf`): sirve para no volver a bajar un modelo cuya revisión no cambió.
- **`LIBRARIES`** de `server/tests/integration/test_venvs.py` lista la librería que importa cada venv (`-m local`).

## 3. Solución

- Huella de receta al instalar y estado `outdated` con «Actualizar» en Motores (D-2).
- Por cada motor, en la carpeta aislada (D-3): subir Python, torch, paquetes, commit y revisión; instalar; correr una salida corta con el candado; medir contra la salida anterior (D-4).
- Recalcular el piso y ajustar ruff, mypy y `test_structure.py` (D-5).

Cada decisión pasa por la escalera de plan-format.md §0 (¿debe existir? ¿ya existe? ¿stdlib o una dependencia que ya está?).

- **D-1: Escalera por motor** — El usuario pidió lo más actual. torch 2.15.0 ya publica cp311–cp315; el límite real son las librerías de cada motor (CosyVoice instala desde su `requirements.txt` y HeartMuLa en modo editable). Se descarta una sola Python para todos los motores, porque obligaría a bajar todos al más restrictivo.
- **D-2: Huella de receta y «Actualizar»** — Hoy nada detecta que una receta cambió (`engines/installer.py`, `verification.py`): cambiar las recetas dejaría al usuario con venvs viejos sin aviso. El trabajo de instalación ya es reanudable. Se descarta reinstalar todo solo al actualizar la app, porque borra y baja decenas de GB sin preguntar (datos del usuario).
- **D-3: Instalación de prueba aislada** — La regla de datos del usuario prohíbe tocar modelos y venvs que la spec no creó. Se descarta probar sobre los motores instalados, porque los reemplaza.
- **D-4: Modelos y repos al día con salida comparada** — Una revisión nueva de un modelo puede cambiar cómo suena; el «debe sonar» decide. Se descarta subir a ciegas, porque el usuario escucha al final y no debe recibir un retroceso.
- **D-5: Piso que sube con las recetas** — Es la condición que puso la 025 para usar sintaxis nueva. Se descarta mantener 3.10 a mano, porque contradice el piso real.

## 4. Fuera de alcance

- Cambiar de motor o de modelo (otra familia, otro tamaño), aunque haya uno mejor: va a `docs/process/02-next/` si aparece.
- Subir CUDA de 12.8 a otra rama si torch no lo exige.
- La API y las dependencias del server (025) y del client (027).

## 5. Criterios de aceptación

- **AC-1**: WHEN se lee cada receta THEN su paso `python` es la versión más alta con la que esa receta instala y genera, y cada motor por debajo de 3.15 tiene su ficha `WARNING/026-<motor>-version.md` con el paquete que lo impide.
- **AC-2**: WHEN se lee cada receta THEN torch, sus paquetes, el commit de git y la revisión de HF son exactos y los más nuevos que pasan AC-4; `test_recipes.py` sigue validando el formato.
- **AC-3**: Given un motor instalado con una receta anterior When se pide `GET /engines` Then el motor sale `outdated`, y `POST /engines/{name}/install` lo reinstala y deja la huella nueva.
- **AC-4**: WHEN cada motor instalado en la carpeta aislada genera su salida corta THEN termina sin error y su duración y LUFS quedan dentro de lo que dice «debe sonar».
- **AC-5**: WHEN se calcula el piso con las recetas nuevas THEN ruff `target-version`, mypy `python_version` y `test_structure.py` usan ese valor.
- **AC-6**: WHEN se corre `uv run pytest -m local` con los venvs aislados THEN cada venv importa su librería.
- **AC-7**: WHEN se abre Motores con un motor `outdated` THEN se ve «Actualización disponible» y el botón «Actualizar», en los tres idiomas.

## 6. Debe sonar / no debe sonar

| Salida | Debe | No debe |
| :--- | :--- | :--- |
| Narración por motor (texto fijo de 2 oraciones, voz de referencia del repo) en `out/narration/<…>-spec-026-<motor>/` | Duración ±15 % y LUFS ±1 LU de la toma con la receta anterior; el texto se entiende (whisper de `evaluation/` sin palabras perdidas) | Cortes, silencios largos, otra voz, clipping |
| Música `acestep` y `heartmula`, 30 s, `lofi-chill` | 30 s ±0,5; LUFS en el rango de `server/data/music/README.md` | Voz o letra, clipping, silencio |
| `faster-whisper` sobre la narración anterior | Mismo texto que antes (±1 palabra) | — |
| Asistente (`llm-eval` con 5 casos) | Respuestas válidas contra su JSON schema | `llm_invalid_output` |

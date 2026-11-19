# 017: verificación final

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación. Cada una queda en [`docs/process/WARNING/`](../../../process/WARNING/README.md); toda revisión pendiente, en [`docs/process/PENDING/`](../../../process/PENDING/README.md).
>
> **Datos del usuario: solo los que crea esta spec**. No borra ni sobrescribe voces grabadas, voces construidas, salidas de `out/` ni modelos que no creó; si algo parece exigirlo, es un `blocked — user-data`. El LLM solo propone.

## 1. Batería

1. `python -m devtools test-runner --type=all`, `--type=e2e`, `--type=budget` y `--type=guard-tdd`.
2. `uv run pytest -m local` (arranca `llama-server` con el modelo ★, pide un JSON simple y lo apaga, con el turno).
3. `uv run studio llm --help | cat` y un caso de error (`studio llm music-caption` sin el modelo instalado sale con exit 1 y `llm_not_installed`).

## 2. Instalación y prueba de modelos (con el turno; las descargas en segundo plano con el log en `logs/`)

1. Desde Motores, instala «Asistente (llama.cpp)» y los dos modelos (unos 11 GB en total). Verifica cada uno y anota la VRAM pico (`nvidia-smi` muestreado) con 8192 de contexto. Si alguno no entra en 8 GB con ese contexto, baja a 4096, anótalo y ajusta `llm/models.py`.
2. `python -m devtools llm-eval` (en segundo plano, con el log en `logs/llm-eval-spec-017.log`). El informe en `tmp/llm-eval/<fecha>/report.md` tiene, por modelo y por tarea, el porcentaje de chequeos que pasan, la latencia, los tok/s y la VRAM.
3. **Revisión humana**: el informe incluye 10 traducciones por modelo lado a lado para que el usuario las puntúe de 1 a 5. Si los chequeos automáticos empatan (diferencia < 5 puntos), el ★ va al de licencia más permisiva y luego al más liviano, con la decisión en `docs/process/WARNING/`; si no, al que más pasa. La puntuación humana se pide sin bloquear.
4. Fija `recommended` en `llm/models.py` con el resultado (commit 9) y escribe WARNING `017-recomendado.md` con las cifras.

## 3. Corridas reales con el ★ (AC-11)

1. **Narración**: un guion de 4 párrafos con cifras, siglas, una oración de 35 palabras y «registras». «Revisar con IA»: acepta 3 párrafos y descarta 1. Narra el resultado y compáralo con el original (escucha del usuario).
2. **Subtítulos**: con el proyecto de la 011, traduce 30 cues al portugués, corrige con un glosario de 3 nombres y sugiere palabras clave. Exporta `.pt.srt`.
3. **Música**: «algo tranquilo con piano y lluvia para un tutorial de cocina», genera una música de 30 s con la sugerencia aceptada y mide la duración y la voz (demucs).
4. **Publicar**: un video de 3 a 5 min de la 010 para YouTube y Reels. Comprueba los límites y los capítulos.
5. Mide la latencia de cada tarea (desde que se pulsa hasta la sugerencia, separando la carga del modelo) y comprueba que tras 2 minutos sin uso `gpu-turn status` queda libre y la VRAM baja.
6. Ejecuta una narración mientras el asistente está caliente: el worker lo apaga antes y no hay dos modelos en la GPU (VRAM muestreada).
7. Capturas de los diffs (guion y subtítulos), de Describir música y de Publicar en claro y en oscuro en `tmp/spec-017/`, que revisa `image-reader`.

## 4. Revisión del usuario

El informe de `llm-eval`, los diffs aceptados y descartados, la narración revisada contra la original, el `.pt.srt` y `publish.json` van en el reporte. El usuario decide si las sugerencias son útiles. Si alguna tarea sale mala con los dos modelos (por ejemplo, la traducción), queda en PENDING con la evidencia y el botón se marca como «experimental» en la UI, en vez de esconder el problema.

## 5. Cierre

* `docs/process/01-done/llm.md`, nueva, y `narration.md` y `subtitles.md` con las funciones de IA.
* Fichas WARNING `017-llama-cpp-version.md` y `017-recomendado.md`, y PENDING `017-vision-miniaturas.md`.
* Se borra `tmp/spec-017/`. El informe de `llm-eval` se resume en la ficha WARNING antes de borrarlo.
* Estado de la fila 017 en el README del lote.

## 6. PR y merge

1. `git fetch origin dev` y merge si avanzó; un solo push.
2. PR a `dev` si no existe, con el informe de `llm-eval`, las capturas, las rutas y las fichas.
3. `gh pr checks <n> --watch` y `gh pr merge <n> --merge`.
4. En el principal: `git switch dev && git pull` y `python -m devtools worktree close 017-local-llm-assist`. Después sigue la 015.
